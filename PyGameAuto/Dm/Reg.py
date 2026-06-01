# Source Generated with Decompyle++
# File: temp.pyc (Python 3.8)

'''
# File       : Reg.py
# Time       ：2022/2/12 15:56
# Author     ：Lex
# email      : 2983997560@qq.com
# Description：大漠插件注册
'''
import os
import ctypes
import win32com.client

class RegDm:
    '''
    大漠对象注册
    '''
    
    def __init__(self):
        pass

    path = os.path.split(os.path.realpath(__file__))[0]
    
    def reg(cls):
        '''
        注册大漠插件并返回大漠对象
        :return:
        '''
        dm = ctypes.windll.LoadLibrary(cls.path + '\\DmReg.dll')
        dm.SetDllPathW(cls.path + '\\dm.dll', 0)
        return win32com.client.DispatchEx('dm.dmsoft')

    reg = classmethod(reg)
    
    def CreateObj(cls):
        '''
        创建大漠对象
        :return: 大漠对象
        '''
        return win32com.client.DispatchEx('dm.dmsoft')

    CreateObj = classmethod(CreateObj)

