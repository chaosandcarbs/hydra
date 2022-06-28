#!/usr/bin/env python3
'''
Hydra - A simple password manager that stores passwords using AES

    main.py

    Requires:
        python3
        pycrypto or pycrptodome
        pickle
        kivy

    To build for windows:
        Requires PyInstaller
        Requires Microsoft Visual C++ Runtimes

    To build for Android:
        Requires Buildozer
        If building in Windows - use wsl as this requires linux
    
'''
from __future__ import unicode_literals
__version__ = '0.1.5'

'''
    Imports
'''
from functools import partial
from kivy.app import App
from kivy.core.clipboard import Clipboard, CutBuffer
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import NumericProperty, StringProperty, BooleanProperty,\
    ListProperty, ObjectProperty
from kivy.uix.popup import Popup
from kivy.utils import platform
from Crypto.Cipher import AES
import os, random, struct, hashlib, pickle, logging
from os.path import dirname



'''
    Globals
'''
fileName = ''
filePath = ''


'''
    Classes
'''

class hydraMain(Screen):
    '''
        hydraMain is the main menu screen
    '''
    msgText = StringProperty()

    def __init__(self, **kwargs):
        super(hydraMain, self).__init__(**kwargs)
        self.msgText = 'Welcome to Hydra!'
        if(self.manager):
            logging.info('Platform: '+self.manager.platform)

    def showLoadFile(self):
        ''' showLoadFile - helper function that triggers popup for loadFile() '''
        content = LoadDialog(loadFile=self.loadFile, cancel=self.dismissPopup)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.72))
        self._popup.open()

    def loadFile(self, path, name):
        ''' loadFile - picks the file to load, and takes user to hydraPassword '''
        if(name == None or name == '' or len(name) == 0):
            pass
        else:
            global filePath
            filePath = path
            global fileName
            logging.info('Entered loadFile')
            if(isinstance(name,list)): #final check; this may be a string or list
                fileName = os.path.basename(name[0])
            else:
                fileName = name

            logging.info('Path: '+filePath)
            logging.info('Name: '+fileName)
            self.dismissPopup()
            nextScreen = 'password'
            self.manager.current = nextScreen


    def showNewFile(self):
        ''' showNewFile - helper function that triggers popup for newFile() '''
        content = NewDialog(newFile=self.newFile, cancel=self.dismissPopup)
        self._popup = Popup(title="New File", content=content,
                            size_hint=(0.9, 0.72))
        self._popup.open()

    def newFile(self, path, filename):
        ''' newFile - picks the file to create, takes user to hydraPasswordNew '''
        if(filename == None or filename == ''):
            pass
        else:
            global filePath
            global fileName
            logging.info('Entered newFile')
            if(path != '' and filename[0] != ''):
                filePath = path
                fileName = filename
            else:
                fileName = 'hydra_passwords'
            self.dismissPopup()
            nextScreen = 'password_new'
            self.manager.current = nextScreen


    def dismissPopup(self):
        ''' dismissPopup - used by popup functions to dismiss themselves '''
        self._popup.dismiss()


class hydraPasswordNew(Screen):
    '''
        hydraPasswordNew covers passwords for new files.

        TODO: This was when I was initially learning Kivy;
            need to remove this and move all functionality
            to the hydraPassword class
    '''
    msgText = StringProperty()
    pwdText = StringProperty()
    pwdText2 = StringProperty()
    def __init__(self, **kwargs):
        super(hydraPasswordNew, self).__init__(**kwargs)
        global fileName
        global filePath
        self.msgText = 'Please Enter a Password For:'+fileName

    def onPwd(self, *args):
        self.hLogin()

    def onPwd2(self, *args):
        self.hLogin()

    def hLogin(self, *args):
        self.pwdText = self.ids.loginInput.text
        self.pwdText2 = self.ids.loginInput2.text
        if(self.pwdText != self.pwdText2):
            self.msgText = "Passwords don't match!"
        else:
            self.msgText = "Passwords match!"
            nextScreen = 'view'
            self.manager.current = nextScreen
            self.manager.lastScreen = 'password_new'

class hydraPassword(Screen):
    '''
        hydraPassword handles password entry for loading files
    '''
    msgText = StringProperty()
    pwdText = StringProperty()
    def __init__(self, **kwargs):
        super(hydraPassword, self).__init__(**kwargs)
        global fileName
        self.msgText = 'Please Enter a Password For: '+fileName

    def onPwd(self, *args):
        self.hLogin()

    def hLogin(self, *args):
        self.pwdText = self.ids.loginInput.text
        self.msgText = 'Attempting decrypt...'
        nextScreen = 'view'
        self.manager.current = nextScreen
        self.manager.lastScreen = 'password'

class hydraView(Screen):
    '''
        hydraView is the primary screen for viewing password information

        Ideally, on load, this will read passwords from the encrypted container
            into a pickle file, load the pickle into memory, and then delete the
            pickle, leaving the original encrypted file on disk while using.

        File writes only happen when a user hits the save button - writing to a
            pickle, encrypted the pickle into another file, and again removing
            the pickle file. The app should then return to the hydraMain screen

        Passwords in memory should be deleted on exit for hitting either the
            save or exit button. Should the app crash, the original encrypted
            container should still exist on disk. 
    '''
    pwdText = StringProperty()
    msgText = StringProperty()
    pList = {}
    sv = ObjectProperty()

    def __init__(self, **kwargs):
        ''' standard init '''
        super(hydraView, self).__init__(**kwargs)

    def on_leave(self, *args):
        ''' on_leave event - make sure we set the variables to empty '''
        global fileName, filePath
        fileName = ''
        filePath = ''
        self.pList = {}
        self.pwdText = ''
        self.listUpdate()

    def on_enter(self, *args):
        ''' on_enter event -

            Check variables are set properly, decrypt the file, load passwords
                into memory. Lastly, update the scrollview with the password
                elements view listUpdate().
        '''
        global fileName, filePath
        if(self.manager != None):
            self.pwdText = self.manager.get_screen(self.manager.lastScreen).ids.loginInput.text
            self.msgText = 'Reading: ' + fileName

            logging.info('lastScreen: '+self.manager.lastScreen)

            if(self.manager.lastScreen == 'password'):
                #load values from the existing file
                logging.info('Loading old file...')
                self.manager.get_screen(self.manager.lastScreen).ids.loginInput.text = ''
                self.openFile()
                self.listUpdate()
            else:
                #no values to load!
                logging.info('New file - nothing to load')
                self.manager.get_screen(self.manager.lastScreen).ids.loginInput.text = ''
                self.manager.get_screen(self.manager.lastScreen).ids.loginInput2.text = ''
                pass

            self.listUpdate()

        else:
            self.msgText = 'Something Went Wrong! No Manager Object'

    def listUpdate(self):
        ''' listUpdate() - Updates the password list in hydraView '''
        logging.info('Updating list of: '+str(len(self.pList)))
        titleWidth = 0.50
        viewWidth = 0.30
        delWidth = 0.20

        self.clean()
        self.passwordList.add_widget(Label(text='Copy Password'))
        self.passwordList.add_widget(Label(text='View Pass'))
        self.passwordList.add_widget(Label(text='Delete'))
        if(len(self.pList.keys()) > 0):
            for site in self.pList.keys():
                logging.info('Adding Site: '+site)

                logging.info('Adding password list to widgets')
                copyCallback = partial(self.copyPass, site)
                self.passwordList.add_widget(Button(text=site, on_release=copyCallback))
                viewCallback = partial(self.viewPass, site)
                self.passwordList.add_widget(Button(text='View', on_release=viewCallback))
                delCallback = partial(self.delPass, site)
                self.passwordList.add_widget(Button(text='Delete', on_release=delCallback))

    def copyPass(self, *args):
        logging.info('Copying: '+args[0])
        Clipboard.copy(self.pList[args[0]])

    def clean(self):
        logging.info('Clearing old widgets')
        self.passwordList.clear_widgets()

    def delPass(self, *args):
        content = DelPassDialog(site=args[0],delete=self.deletePassword, cancel=self.dismissPopup)
        self._popup = Popup(title="Delete Password", content=content,
                            size_hint=(0.7,0.3))
        self._popup.open()

    def deletePassword(self, *args):
        logging.info('Deleting: '+args[0])
        del self.pList[args[0]]
        self.listUpdate()
        self.dismissPopup()


    def viewPass(self, *args):
        content = ViewPassDialog(site=args[0],pword=self.pList[args[0]],
                                copy=self.copyPass, cancel=self.dismissPopup)
        self._popup = Popup(title="View Password", content=content,
                            size_hint=(0.7,0.30))
        self._popup.open()

    def showSaveFile(self):
        content = SaveDialog(saveFile=self.saveFile,cancel=self.dismissPopup)
        self._popup = Popup(title="Save File", content=content,
                            size_hint=(0.7,0.25))
        self._popup.open()

    def newPass(self, siteInput):
        if(siteInput != ''):
            self.pList[siteInput] = self.genPass()
            self.dismissPopup()
            self.listUpdate()

    def showNewPass(self):
        content = NewPassDialog(newPass=self.newPass,cancel=self.dismissPopup)
        self._popup = Popup(title="Creat New Password", content=content,
                            size_hint=(0.7,0.25))
        self._popup.open()

    def genPass(self):
        ''' genPass - generates a random password '''
        #TODO: make length/alphabet variable via setting.
        #   Note that length generally trumps complexity; this should suffice for now
        alphabet = "abcdefghijklmnopqrstuvwxzyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789[]()"
        length = 30
        pw = ""
        for i in range(length):
            pw = pw + alphabet[random.randrange(len(alphabet))]
        return pw

    def dismissPopup(self):
        self._popup.dismiss()

    def saveFile(self):
        global filePath
        global fileName
        key = hashlib.sha256(self.pwdText.encode('utf-8')).digest()
        decFile = os.path.join(filePath,fileName+'.pickle')
        with open(decFile,'wb') as sHandle:
            pickle.dump(self.pList, sHandle)
        sHandle.close()
        self.encryptFile(key, decFile, os.path.join(filePath,fileName))
        os.remove(decFile)
        self.dismissPopup()
        nextScreen = 'main'
        self.manager.current = nextScreen

    def openFile(self):
        global fileName
        global filePath

        self.pList = {}
        key = hashlib.sha256(self.pwdText.encode('utf-8')).digest()
        encFile = os.path.join(filePath,fileName)
        decFile = encFile+".pickle"
        logging.info('encfile: '+encFile)
        logging.info('decFile: '+decFile)
        try:
            self.decryptFile(key, encFile, decFile)
            logging.info('Opening pickle')
            with open(decFile,'rb') as oHandle:
                self.pList = pickle.load(oHandle)
            oHandle.close()
            logging.info('Closing pickle')
        except (pickle.UnpicklingError, ImportError, EOFError, IndexError, TypeError):
            logging.warn('Password incorrect or pickling failed')
            self.msgText = "Bad Password: The password you entered failed decryption, or pickling failed"
        logging.info('Removing temp pickle file')
        os.remove(decFile)
        logging.info('Updating list')
        self.listUpdate()

    #source: https://eli.thegreenplace.net/2010/06/25/aes-encryption-of-files-in-python-with-pycrypto/
    def decryptFile(self,key, in_filename, out_filename=None, chunksize=24*1024):
        logging.info('Attempting decrypt')
        if not out_filename:
            out_filename = os.path.splitext(in_filename)[0]

        with open(in_filename, 'rb') as infile:
            origsize = struct.unpack('<Q', infile.read(struct.calcsize('Q')))[0]
            iv = infile.read(16)
            decryptor = AES.new(key, AES.MODE_CBC, iv)

            with open(out_filename, 'wb') as outfile:
                while True:
                    chunk = infile.read(chunksize)
                    if len(chunk) == 0:
                        break
                    outfile.write(decryptor.decrypt(chunk))

                outfile.truncate(origsize)
        logging.info('Decrypt routine finished')

    #Source: https://eli.thegreenplace.net/2010/06/25/aes-encryption-of-files-in-python-with-pycrypto/
    def encryptFile(self,key, in_filename, out_filename=None, chunksize=64*1024):
        if not out_filename:
            out_filename = in_filename + '.hydra'

        iv = bytes(os.urandom(16))
        encryptor = AES.new(key, AES.MODE_CBC, iv)
        filesize = os.path.getsize(in_filename)

        with open(in_filename, 'rb') as infile:
            with open(out_filename, 'wb') as outfile:
                outfile.write(struct.pack('<Q', filesize))
                outfile.write(iv)

                while True:
                    chunk = infile.read(chunksize)
                    if len(chunk) == 0:
                        break
                    elif len(chunk) % 16 != 0:
                        chunk += bytes((' ' * (16 - len(chunk) % 16)).encode('utf-8'))
                    outfile.write(encryptor.encrypt(chunk))

class ViewPassDialog(FloatLayout):
    site = ObjectProperty(None)
    pword = ObjectProperty(None)
    copy = ObjectProperty(None)
    cancel = ObjectProperty(None)

class NewPassDialog(FloatLayout):
    newPass = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)

class DelPassDialog(FloatLayout):
    site = ObjectProperty(None)
    delete = ObjectProperty(None)
    cancel = ObjectProperty(None)

class LoadDialog(FloatLayout):
    loadFile = ObjectProperty(None)
    cancel = ObjectProperty(None)


class SaveDialog(FloatLayout):
    saveFile = ObjectProperty(None)
    cancel = ObjectProperty(None)

class NewDialog(FloatLayout):
    newFile = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)


class hydraApp(App):
    sm = ScreenManager()
    lastScreen = ''
    filePathStart = ''
    filePathSeparator = ''
    curPlatform = ''

    def __init__(self, **kwargs):
        super(hydraApp, self).__init__(**kwargs)

    def build(self):
        self.title = 'Hydra v0.1'
        Builder.load_file(os.path.join(dirname(__file__), 'main.kv'))
        self.sm = ScreenManager()
        self.sm.lastScreen = ''
        self.platformChecks()
        self.sm.platform = self.curPlatform
        #TODO Fix the call here - self.manager.fpSeparator isn't ideal
        self.sm.add_widget(hydraMain(name='main'))
        self.sm.add_widget(hydraPassword(name='password'))
        self.sm.add_widget(hydraPasswordNew(name='password_new'))
        self.sm.add_widget(hydraView(name='view'))
        self.sm.current = 'main'
        return self.sm

    def platformChecks(self, *args):
        if platform == 'android':
            self.filePathStart = '/storage/emulated/0/'
            from android.permissions import request_permissions, Permission, check_permission
            from android import loadingscreen
            perms = [Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE]
            for perm in perms:
                if check_permission(perm) != True:
                    logging.info('Failed permission: '+perm)
                    request_permissions(perms)
                    exit()
            loadingscreen.hide_loading_screen()
            filePathSeparator = '/'
            Window.fullscreen = 'auto'
        elif platform == 'win':
            self.filePathStart = '/'
            Window.size = (600,800)
        else:
            self.filePathStart = '.'
        self.curPlatform = platform

    def on_request_close(self, *args):
        content = SaveDialog(saveFile='',text_input='',cancel=self.dismissPopup)
        self._popup = Popup(title='Exit',content=content)
        return True



if __name__ == '__main__':
    hydraApp().run()
