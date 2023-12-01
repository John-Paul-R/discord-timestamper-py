# This example requires the 'message_content' intent.
import datetime
import json
import os
import time

import discord
import parsedatetime
from discord.abc import Snowflake

from timestamper.main import try_parsedatetime

intents = discord.Intents.default()
intents.message_content = True

if __name__ == '__main__':
    client = discord.Client(intents=intents)

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


def adjust_time_for_user(t: float, user_id: Snowflake):
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
async def on_message(message):
    if message.author == client.user:
        return

    content: str = message.content

    if content.startswith('$hello'):
        await message.channel.send('Hello!')

    if content.startswith('$set_utc_offset'):
        tz_to_parse = content[len('$set_utc_offset'):].strip()
        try:
            tz_offset = float(tz_to_parse)
            set_user_tz_offset(message.author.id, tz_offset)
            await message.channel.send(f"Set your time zone offset to '{tz_offset}'.")
        except:
            await message.channel.send(
                f"Failed to parse '{tz_to_parse}' to a time zone offset"
                "\n(hint: try a number in the range [-12.0, 14.0], e.g. '5.0')")

    short_idx = content.find('$t')
    full_idx = content.find('$time', short_idx)
    (idx, l) = (full_idx, len('$time')) if full_idx != -1 else (short_idx, len('$t'))
    if idx != -1:
        res = try_parsedatetime(content[l:])
        st: time.struct_time = res[0]
        status: parsedatetime.pdtContext = res[1]
        if status.hasDate and status.hasTime:
            # time_str = time.strftime('%Y-%m-%dT%H:%M:%SZ', timestamp)
            # t = datetime(*timestamp[:6])
            epoch_time = adjust_time_for_user(time.mktime(st), message.author.id)
            await message.channel.send(
                "Time: <t:{:.0f}:F> (<t:{:.0f}:R>)".format(epoch_time, epoch_time))
        else:
            matched_str = content[idx:idx + l]
            await message.channel.send(
                f"found string '{matched_str}', but no time data could be detected in the message!")


# https://discord.com/developers/applications/1179887574270099486/oauth2/general
client.run(os.environ['DISCORD_BOT_TOKEN'])
