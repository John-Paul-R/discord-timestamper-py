# This example requires the 'message_content' intent.
import datetime
import json
import os
import queue
import threading
import time
from time import mktime

import discord
import parsedatetime
from discord.ext import tasks as discord_tasks

from timestamper.main import try_parsedatetime
from timestamper.ts_discord.graceful_killer import GracefulKiller
from .celeryinit import app as c

killer = GracefulKiller()

intents = discord.Intents.default()
intents.message_content = True

celery_pending_tasks = queue.Queue()


@discord_tasks.loop(seconds=5.0)
async def slow_count():
    global killer
    print(f"Killnow? {killer.kill_now}")
    if killer.kill_now:
        await client.close()
    global celery_pending_tasks
    print(f"{slow_count.current_loop}: taskCount:{celery_pending_tasks.unfinished_tasks}")

    while not celery_pending_tasks.empty():
        try:
            print("awaiting a task!")
            await celery_pending_tasks.get()
            celery_pending_tasks.task_done()
        except:
            print("UNEXDPECTED TASK ERROR IM LOSING MY MIND")


@slow_count.after_loop
async def after_slow_count():
    print('Exiting discord task processing loop')


class MyClient(discord.Client):
    global celery_pending_tasks

    async def setup_hook(self):
        slow_count.start()


client = MyClient(intents=intents)

_start_time = datetime.datetime.now().timestamp()
system_utc_offset = (
        datetime.datetime.utcfromtimestamp(_start_time) -
        datetime.datetime.fromtimestamp(_start_time)
).total_seconds()

users_tz_path = "./user_timezoneoffsets.json"
should_init = os.path.getsize(users_tz_path) == 0
if should_init:
    with open(users_tz_path, mode='w+') as f:
        f.write('{}')
        f.flush()
        f.close()

with open(users_tz_path, mode='r') as f:
    user_timezones: dict[str, float] = json.load(f)
    print(json.dumps(user_timezones))


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


one_minute_secs = 60
one_hour_secs = 60 * one_minute_secs


def adjust_time_for_user(t: float, user_id: int):
    user_tz_offset_hrs = user_timezones[str(user_id)]
    if user_tz_offset_hrs is None:
        return t
    print(t, system_utc_offset, user_tz_offset_hrs)
    return t - (system_utc_offset + one_hour_secs * user_tz_offset_hrs)


def set_user_tz_offset(user_id: int, tz_offset: float):
    user_timezones[str(user_id)] = tz_offset
    with open("./user_timezoneoffsets.json", mode='w') as f:
        json.dump(user_timezones, f)
        f.flush()
        f.close()


def get_user_tz_offset(user_id: int):
    user_timezones.get(str(user_id))


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    content = message.content

    if content.startswith('$hello'):
        await message.channel.send('Hello!')

    if content.startswith('$timeit'):
        await cmd_timeit(message, content[len('$timeit'):])
    elif '$time' in content:
        await cmd_time(message, content[content.index("$time") + len('$time'):])
    elif '$t' in content:
        await cmd_time(message, content[content.index("$t") + len('$t'):])
    elif content.startswith('$set_utc_offset'):
        await cmd_set_utc_offset(message, content[len('$set_utc_offset'):])
    elif content.startswith('$remindme'):
        await cmd_remindme(message, content[len('$remindme'):])


async def cmd_set_utc_offset(message: discord.Message, cmd_content: str):
    tz_to_parse = cmd_content.strip()
    try:
        tz_offset = float(tz_to_parse)
        set_user_tz_offset(message.author.id, tz_offset)
        await message.channel.send(f"Set your time zone offset to '{tz_offset}'.")
    except:
        await message.channel.send(
            f"Failed to parse '{tz_to_parse}' to a time zone offset"
            "\n(hint: try a number in the range [-12.0, 14.0], e.g. '5.0')")


async def cmd_time(message: discord.Message, cmd_content: str):
    await exec_cmd_time(message, cmd_content)


def extract_time_from_msg(message: discord.Message, meaningful_time_content: str):
    res = try_parsedatetime(meaningful_time_content)
    st: time.struct_time = res[0]
    status: parsedatetime.pdtContext = res[1]
    if status.hasDate and status.hasTime:
        # time_str = time.strftime('%Y-%m-%dT%H:%M:%SZ', timestamp)
        # t = datetime(*timestamp[:6])
        epoch_time = adjust_time_for_user(mktime(st), message.author.id)
        return epoch_time
    else:
        return None


async def exec_cmd_time(message: discord.Message, meaningful_time_content: str):
    epoch_time = extract_time_from_msg(message, meaningful_time_content)
    if epoch_time is None:
        await message.channel.send("no time data detected in message")
        # matched_str = message.content[idx:idx + l]
        # await message.channel.send(
        #     f"found string '{matched_str}', but no time data could be detected in the message!")
    else:
        # time_str = time.strftime('%Y-%m-%dT%H:%M:%SZ', timestamp)
        # t = datetime(*timestamp[:6])
        await message.channel.send(
            "Time: <t:{:.0f}:F> (<t:{:.0f}:R>)".format(epoch_time, epoch_time))


async def _get_target_ref_msg_id(message: discord.Message, url_candidate_text: str) -> int:
    if message.reference is not None:
        return message.reference.message_id

    return int(message_id_from_link(url_candidate_text.strip()))


async def get_target_ref_msg(message: discord.Message, url_candidate_text: str):
    reply_msg_id = await _get_target_ref_msg_id(message, url_candidate_text)
    print(reply_msg_id)
    return await message.channel.fetch_message(reply_msg_id)


async def cmd_timeit(message: discord.Message, cmd_content: str):
    target_msg = await get_target_ref_msg(message, cmd_content)
    await exec_cmd_time(message, target_msg.content)


def message_id_from_link(link: str) -> str:
    return link[link.rindex('/') + 1:]


async def cmd_remindme(message: discord.Message, cmd_content: str):
    target_message = await get_target_ref_msg(message, cmd_content)
    t = datetime.datetime.fromtimestamp(
        extract_time_from_msg(target_message, target_message.content)
        + system_utc_offset
    )
    print(t)
    await schedule_reminder(
        user_id=target_message.author.id,
        message_id=message.id,
        guild_id=message.guild.id,
        channel_id=message.channel.id,
        t=t.replace(tzinfo=datetime.timezone.utc)
    )


async def schedule_reminder(
        user_id: int,
        guild_id: int,
        channel_id: int,
        message_id: int,
        t: datetime.datetime
):
    guild = await client.fetch_guild(guild_id)
    channel = await guild.fetch_channel(channel_id)
    msg_to_remind = await channel.fetch_message(message_id)
    await channel.send("confirmation that the system got your message", reference=msg_to_remind)

    do_reminder.apply_async(args=[guild_id, channel_id, message_id],
                            eta=t)


@c.task
def do_reminder(
        guild_id: int,
        channel_id: int,
        message_id: int,
):
    global celery_pending_tasks
    print("CELERY START HANDLE TASK")
    celery_pending_tasks.put(do_reminder_impl(
        guild_id,
        channel_id,
        message_id,
    ))
    print(f"yknow, but I gotta check {celery_pending_tasks.unfinished_tasks}")


from celery.signals import worker_shutdown


@worker_shutdown.connect
def do_graceful_exit(**kwargs):
    killer.exit_gracefully()


async def do_reminder_impl(
        guild_id: int,
        channel_id: int,
        message_id: int,
):
    print(f"REMINDER START, {guild_id}, {channel_id}, {message_id}, {client.is_closed()}")
    channel = client.get_guild(guild_id) \
        .get_channel(channel_id)
    msg_to_remind = await channel.fetch_message(message_id)
    await channel.send("Reminder!", reference=msg_to_remind)


if __name__ == '__main__':
    # https://discord.com/developers/applications/1179887574270099486/oauth2/general
    print("Starting discord bot")
    client.run(os.environ['DISCORD_BOT_TOKEN'])
else:  # running via celery
    print("Starting separate discord bot thread")
    thread = threading.Thread(target=client.run, args=[os.environ['DISCORD_BOT_TOKEN']])
    thread.start()
