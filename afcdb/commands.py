# -*- coding: utf-8 -*-
import asyncio
import traceback
import jsons
import re
import requests
from discord import ChannelType, Message
from datetime import datetime

from afcdb import consts
from afcdb.utils import AFCDBConfig
from afcdb.utils import Utils


class Command:
    """
    Botのコマンドクラス.
    """
    __config: AFCDBConfig
    __has_args: bool
    __cmd: str

    @property
    def config(self):
        return self.__config

    @property
    def cmd(self):
        return self.__cmd

    @property
    def has_args(self):
        return self.__has_args

    def __init__(self, config, cmd, has_args):
        """
        コンストラクタ.
        :param config: コンフィグ管理インスタンス.
        :type config: AFCDBConfig
        :param cmd: コマンド.
        :type cmd: str
        :param has_args: コマンドが変数を受け取るか.
        :type has_args: bool
        """
        self.__config = config
        self.__cmd = cmd
        self.__has_args = has_args

    def usage(self):
        """
        使い方を返却する.
        各コマンドで説明を実装してください.
        :return: コマンドの使い方
        :rtype: str
        """
        raise NotImplementedError('コマンドサブクラスでexecute_cmdを実装してください.')

    def is_call(self, msg):
        """
        コマンドが呼び出されたか.
        :param msg: 書き込まれたメッセージ
        :type msg: str
        :return: 処理結果
        :rtype: bool
        """
        return msg.startswith(self.cmd)

    def is_cmd_help(self, msg):
        """
        コマンドのヘルプが呼び出されたか.
        :param msg: 書き込まれたメッセージ
        :type msg: str
        :return: 判定結果
        :rtype: bool
        """
        return self.cmd + " /?" == msg

    def is_valid(self, message):
        """
        バリデーションを行う.
        引数なしの場合、メッセージとコマンドが一致するか.
        引数ありの場合、メッセージがコマンド+空白で始まり、かつ、メッセージ長がコマンド+空白以上か.
        :param message: Discordメッセージインスタンス
        :type message: Message
        :return: 判定結果
        :rtype: bool
        """
        if self.has_args:
            return message.content.startswith(self.cmd + " ") and len(self.cmd) + 1 < len(message.content)
        else:
            return message.content == self.cmd

    def valid_custom(self, message, args):
        """
        コマンド固有のバリデーションを行う.
        引数ありのコマンドの場合、このメソッドをオーバーライドしてバリデーションを実装してください.
        :param message: Discordメッセージインスタンス
        :type message: Message
        :param args: コマンド引数
        :type args: str
        :return: 検証失敗時のメッセージ.検証成功の場合はNone.
        :rtype: str
        """
        return None

    async def execute(self, message):
        """
        コマンドを実行する.
        :param message: Discordメッセージインスタンス
        :type message: Message
        """
        print(self.cmd + " call.")
        if not message and not message.content:
            print("【エラー】Discordからコマンドが受け取れません. 再度入力してください.")
            return False
        if self.is_cmd_help(message.content):
            await message.channel.send(self.usage())
            print(self.cmd + " show help.")
            return False
        if not self.is_valid(message):
            msg = "コマンドが正しくありません.\n" + self.usage()
            await message.channel.send(msg)
            print(self.cmd + " failed valid.")
            return False
        args = message.content[len(self.cmd) + 1:]
        valid_msg = self.valid_custom(message, args)
        if valid_msg:
            msg = valid_msg + "\n" + self.usage()
            await message.channel.send(msg)
            print(self.cmd + " failed valid_custom.")
            return False
        await self.execute_cmd(message, args)
        print(self.cmd + " called.")

    async def execute_cmd(self, message, args):
        """
        コマンド固有の処理を実行する.
        各コマンドはメインの処理をここに実装してください.
        :param message: Discordメッセージインスタンス
        :type message: Message
        :param args: コマンド引数
        :type args: str
        :return: 処理結果
        :rtype: bool
        """
        raise NotImplementedError('コマンドサブクラスでexecute_cmdを実装してください.')


class AllCommand(Command):
    """
    全コマンドを扱うコマンドクラス
    """

    __cmd_list: list

    @property
    def cmd_list(self):
        return self.__cmd_list

    def __init__(self, config, cmd, has_args, cmd_list):
        super().__init__(config, cmd, has_args)
        self.__cmd_list = cmd_list


class CommandManager:
    """
    コマンド管理クラス.
    コマンド実行はこのクラスの execute() にメッセージを食わせる.
    """

    __config: AFCDBConfig
    __cmd_list: list
    __help_cmd: Command

    def __init__(self, config):
        """
        コンストラクタ.
        コマンドクラス追加時は __cmd_list にコマンドインスタンスを追加すること.
        :param config: コンフィグ管理インスタンス
        :type config: AFCDBConfig
        """

        self.__config = config
        self.__cmd_list = [
            ListNoticeCommand(config),
            AddNoticeCommand(config),
            DelNoticeCommand(config)
        ]
        self.__help_cmd = HelpCommand(config, self.__cmd_list)
        self.__cmd_list.append(self.__help_cmd)

    async def execute(self, message):
        """
        コマンド実行.
        :param message: Discordのメッセージインスタンス
        :type message: Message
        :return: 処理結果
        :rtype: bool
        """

        # コマンド呼び出し判定
        if not message.content.startswith("/"):
            return False

        # コマンド判定
        call_cmd = None
        for cmd in self.__cmd_list:
            if cmd.is_call(message.content):
                call_cmd = cmd
                break
        if not call_cmd:
            # コマンドが存在しない場合ヘルプ表示
            msg = "コマンドが正しくありません.\n" + self.__help_cmd.usage()
            await message.channel.send(msg)
            return False

        return await call_cmd.execute(message)


class HelpCommand(AllCommand):
    """
    ヘルプを表示する.
    """

    def __init__(self, config, cmd_list):
        ret = []
        for cmd in cmd_list:
            if type(cmd) == HelpCommand:
                continue
            ret.append(cmd)
        super().__init__(config, "/?", False, ret)

    def usage(self):
        msg = "`/?`" \
              "\nヘルプを表示します.\n/start /? のように入力するとコマンドのヘルプを表示します."
        return msg

    async def execute_cmd(self, message, args):
        ret = []
        ret.append(self.usage() + "\n")
        for cmd in self.cmd_list:
            ret.append(cmd.usage() + "\n")
        msg = "\n".join(ret)
        await message.channel.send(msg)
        return True


class AddNoticeCommand(Command):
    """
    カンパニーログ通知条件追加コマンド.
    """

    def __init__(self, config, cmd=None, has_args=False):
        super().__init__(config, cmd if cmd else "/add notice", has_args if has_args else True)

    def usage(self):
        msg = "`/add notice [通知条件] [通知メッセージ]`" \
              "\n通知条件を追加します." \
              "\n通知条件がすでに存在する場合、上書き登録を行います."\
              "\nカンパニーログに通知条件が一致した場合、通知メッセージを送信します." \
              "\n通知条件は「Your * was destroyed!」のように *(アスタリスク)を使用して条件設定が行います." \
              "\n通知メッセージは「下記が破壊されました！ %%1」のように設定します."\
              "\n%%1は通知条件のアスタリスクの文言が表示されます."\
              "\n「/add notice \"Your * was destroyed by *\" \"＠here %%1が%%2に破壊されました！\"」が設定されている際に"\
              "カンパニーログに「Your Bed was destroyed by ABC」が表示された場合、"\
              "通知チャンネルに「＠here BedがABCに破壊されました！」と表示されます."\
              "\n＠hereのアットマークは全角で入力してください.コマンド入力時のhere通知を避けるためです."
        return msg

    def valid_custom(self, message, args):
        if not args :
            return "正しく入力してください."
        arg_list = Utils.split_args(args)
        s1 = arg_list[0] if len(arg_list) >= 1 else ""
        s2 = arg_list[1] if len(arg_list) >= 2 else ""
        if not s1 or not s2:
            return "通知条件や通知メッセージを正しく設定してください."

    async def execute_cmd(self, message, args):
        arg_list = Utils.split_args(args)
        s1 = arg_list[0]
        s2 = arg_list[1]
        s2 = s2.replace("＠", "@")

        is_add = True
        msg = ""
        for f in self.config.notice_filters:
            if f == s1:
                is_add = False
                break
        if is_add:
            self.config.add_notice_filter(s1, s2)
            msg = "通知条件を追加しました."
        else:
            self.config.del_notice_filter(s1)
            self.config.add_notice_filter(s1, s2)
            msg = "通知条件を上書きしました."
        await message.channel.send(msg)
        return True


class DelNoticeCommand(Command):
    """
    カンパニーログ通知条件削除コマンド.
    """

    def __init__(self, config, cmd=None, has_args=False):
        super().__init__(config, cmd if cmd else "/del notice", has_args if has_args else True)

    def usage(self):
        msg = "`/del notice [通知条件]`" \
              "\n通知条件を削除します."
        return msg

    def valid_custom(self, message, args):
        if not args:
            return "正しく入力してください."

    async def execute_cmd(self, message, args):
        arg_list = Utils.split_args(args)
        s1 = arg_list[0] if len(arg_list) >= 1 else ""
        self.config.del_notice_filter(s1)
        msg = "通知条件を削除しました."
        await message.channel.send(msg)
        return True


class ListNoticeCommand(Command):
    """
    カンパニーログ通知条件一覧表示コマンド.
    """

    def __init__(self, config, cmd=None, has_args=False):
        super().__init__(config, cmd if cmd else "/list notice", has_args if has_args else False)

    def usage(self):
        msg = "`/list notice`" \
              "\n通知条件の一覧を表示します."
        return msg

    async def execute_cmd(self, message, args):
        ret = []
        i = 1
        for s in self.config.notice_filters:
            ret.append("【条件{}】\n{}\n【通知{}】\n{}".format(str(i), s, str(i), self.config.notice_filters[s]))
            i += 1
        s = "\n".join(ret)
        msg = "通知条件:\n{}".format(s)
        msg = msg.replace("@", "＠")
        await message.channel.send(msg)
        return True
