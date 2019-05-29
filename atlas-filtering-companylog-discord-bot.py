# -*- coding: utf-8 -*-
import os
import discord
from discord import ChannelType, Client, Message
from afcdb import commands, consts
from afcdb.utils import AFCDBConfig, Utils
import traceback


# global var
client: Client = discord.Client()
config: AFCDBConfig = AFCDBConfig(client)
cmd_manager: commands.CommandManager = commands.CommandManager(config)


@client.event
async def on_ready():
    """
    Discordクライアント初期化イベント
    :return: None
    :rtype: None
    """
    print('起動開始...')
    print('ユーザ名:', client.user.name)
    print('ユーザID:', client.user.id)
    print('------')

    try:
        print("ログ出力フォルダ作成.")
        os.makedirs(consts.LOG_FOLDER, exist_ok=True)

        guilds = Utils.get_none_notice_channel_servers(client, config)
        if guilds:
            print("Bot通知チャンネル追加...")
            for guild in guilds:
                await guild.create_text_channel(config.notice_channel_name)
            print("Bot通知チャンネル追加完了.")

        msg = "起動.\nこのチャンネルに重要なカンパニーログの通知やコマンドを実行します.\n/? を入力すると使い方を表示します."
        channels = Utils.get_channels(client, config.notice_channel_name)
        for channel in channels:
            await channel.send(msg)

        if not Utils.get_channels(client, config.watch_channel_name):
            print("カンパニーログチャンネルが存在しない.")
            msg = "【警告】カンパニーログチャンネルが存在しません.\nコマンドからカンパニーログチャンネルを設定してください.(現在設定値:" + config.watch_channel_name + ")"
            await channel.send(msg)

    except Exception as e:
        print("【エラー】on_ready. 処理終了.")
        with open(consts.LOG_FILE, 'a') as f:
            traceback.print_exc(file=f)
        exit(1)


@client.event
async def on_message(message):
    """
    メッセージ書き込みイベント
    :param message: 書き込まれたメッセージ
    :type message: Message
    :return: None
    :rtype: None
    """
    try:
        if message.channel.name.upper() == config.watch_channel_name:
            print("watch_channelメッセージ受信.\n" + message.content)
            clog_list = message.content.split("\n")
            for clog in clog_list:
                for f in config.notice_filters:
                    s = clog
                    f_words = f.split("*")
                    f_args = []
                    is_match = True
                    for f_word in f_words:
                        find_index = s.find(f_word)
                        if find_index == -1:
                            is_match = False
                            break
                        f_args.append(s[:find_index])
                        s = s[find_index + len(f_word):]
                    if not is_match:
                        continue
                    f_args.append(s)

                    msg = config.notice_filters[f]
                    for i in range(0, 10):
                        if len(f_args) <= i:
                            break
                        msg = msg.replace('%%' + str(i), f_args[i])

                    channels = Utils.get_channels(client, config.notice_channel_name)
                    for channel in channels:
                        await channel.send(msg)
                    print("notice_channelメッセージ送信.\n" + msg)
                    break
            return
        if message.channel.name.upper() == config.notice_channel_name and not message.author.bot:
            await cmd_manager.execute(message)
            return
    except Exception as e:
        print("【エラー】on_message. 処理継続.")
        with open(consts.LOG_FILE, 'a') as f:
            traceback.print_exc(file=f)
        client.send_message(message.channel, "【エラー】複数回発生したら再起動か管理者に報告よろ.")


if __name__ == "__main__":
    client.run(config.token)
