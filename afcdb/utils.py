# -*- coding: utf-8 -*-
import configparser
import json

from discord import Client
from afcdb import consts


class AFCDBConfig:
    """
    コンフィグ管理クラス.
    """

    def __init__(self, client_val):
        self.__config = configparser.RawConfigParser()
        self.__config.read(consts.CONFIG_FILE_NAME, encoding='utf-8')
        self.__token = str(self.config.get(consts.SECTION_NAME, consts.KEY_TOKEN))
        self.__notice_channel_name = str(self.config.get(consts.SECTION_NAME, consts.KEY_NOTICE_CHANNEL_NAME))
        self.__watch_channel_name = str(self.config.get(consts.SECTION_NAME, consts.KEY_WATCH_CHANNEL_NAME))
        self.__notice_filters = json.loads(self.config.get(consts.SECTION_NAME, consts.KEY_NOTICE_FILTERS))
        self.__client = client_val

    @property
    def config(self):
        return self.__config

    @property
    def token(self):
        return self.__token

    @property
    def notice_channel_name(self):
        return self.__notice_channel_name

    @notice_channel_name.setter
    def notice_channel_name(self, notice_channel_name):
        self.__notice_channel_name = notice_channel_name
        self.write()

    @property
    def watch_channel_name(self):
        return self.__watch_channel_name

    @watch_channel_name.setter
    def watch_channel_name(self, watch_channel_name):
        self.__watch_channel_name = watch_channel_name
        self.write()

    @property
    def notice_filters(self):
        return self.__notice_filters

    def add_notice_filter(self, filter_word, output_word):
        """
        フィルターを追加します.
        :param filter_word: 通知対象の文字列
        :type filter_word: str
        :param output_word: 通知時の文字列
        :type output_word: str
        :return: 処理が成功したかどうか
        :rtype: bool
        """
        if not filter_word or not output_word:
            return False
        for s in self.notice_filters:
            if s == filter_word:
                return False
        self.notice_filters[filter_word] = output_word.strip()
        self.write()
        return True

    def del_notice_filter(self, filter_word):
        """
        フィルターを削除します.
        :param filter_word: 通知対象の文字列
        :type filter_word: str
        :return: 処理が成功したかどうか
        :rtype: bool
        """
        if not filter_word:
            return False
        for s in self.notice_filters:
            if s == filter_word:
                self.notice_filters.pop(filter_word)
                self.write()
                return True
        return False

    @property
    def client(self):
        return self.__client

    def write(self):
        """
        コンフィグを書き込む.
        :return: None
        :rtype: None
        """
        configw = configparser.ConfigParser()
        configw.add_section(consts.SECTION_NAME)
        configw.set(consts.SECTION_NAME, consts.KEY_TOKEN, self.token)
        configw.set(consts.SECTION_NAME, consts.KEY_NOTICE_CHANNEL_NAME, str(self.notice_channel_name))
        configw.set(consts.SECTION_NAME, consts.KEY_WATCH_CHANNEL_NAME, str(self.watch_channel_name))
        configw.set(consts.SECTION_NAME, consts.KEY_NOTICE_FILTERS, json.dumps(self.notice_filters))
        with open(consts.CONFIG_FILE_NAME, 'w', encoding='utf-8') as configfile:
            configw.write(configfile)


class Utils:
    @classmethod
    async def send_message(cls, channel, msg):
        """
        Discordにメッセージを送信する.
        :param channel: メッセージを送信するチャンネルインスタンス
        :type channel: Channel
        :param msg: 送信するメッセージ
        :type msg: str
        :return: None
        :rtype: None
        """
        await channel.send(msg)

    @classmethod
    def get_none_notice_channel_servers(cls, client, config):
        """
        Bot通知チャンネルのないサーバのリストを取得する.
        :param client: Disordのクライアントオブジェクト
        :type client: Client
        :return: ギルドのリスト
        :rtype: list os Discord.Guild
        """
        print('get_none_notice_channel_servers call...')
        ret = []
        for guild in client.guilds:
            has_cmd_channel = False
            for channel in guild.text_channels:
                if channel.name not in config.notice_channel_name:
                    continue
                has_cmd_channel = True
                break
            if not has_cmd_channel:
                ret.append(guild)
        return ret

    @classmethod
    def get_channels(cls, client, channel_name):
        """
        各ギルドの指定されたチャンネルのリストを取得する.
        :param: client Client
        :type: client Client
        :param: channel_name チャンネル名
        :type: channel_name str
        :return: チャンネルのリスト
        :rtype: list of Channel
        """
        print('get_notice_channels call...')
        ret = []
        for guild in client.guilds:
            for channel in guild.text_channels:
                if channel.name.upper() != channel_name.upper():
                    continue
                ret.append(channel)
                break
        return ret

    @classmethod
    def split_args(self, args):
        """
        引数を分割する.
        :param args: 引数
        :type args: str
        :return: 分割した引数
        :rtype: list of str
        """
        ret = []
        if args.find("\"") >= 0:
            arg = ""
            in_dq = False
            for s in args:
                if s == " " and not in_dq:
                    ret.append(arg)
                    arg = ""
                    continue
                if s == "\"":
                    in_dq = not in_dq
                    continue
                arg += s
            if arg:
                ret.append(arg)
        else:
            ret = args.split(" ")
            if not ret:
                return None
        return ret
