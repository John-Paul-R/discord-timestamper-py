# This example requires the 'message_content' intent.
import os
import time

import discord
import parsedatetime

from timestamper.main import try_parsedatetime

intents = discord.Intents.default()
intents.message_content = True

if __name__ == '__main__':
    client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    content: str = message.content
    if '$time' in content:
        res = try_parsedatetime(content[len('$time'):])
        st: time.struct_time = res[0]
        status: parsedatetime.pdtContext = res[1]
        if status.hasDateOrTime:
            # time_str = time.strftime('%Y-%m-%dT%H:%M:%SZ', timestamp)
            # t = datetime(*timestamp[:6])
            epoch_time = time.mktime(st)
            await message.channel.send(
                "Time: <t:{:.0f}:F> (<t:{:.0f}:R>)".format(epoch_time, epoch_time))
        else:
            await message.channel.send(
                "found string '$time', but no time data could be detected in the message!")


# https://discord.com/developers/applications/1179887574270099486/oauth2/general
client.run(os.environ['DISCORD_BOT_TOKEN'])
