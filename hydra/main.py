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
__version__ = '0.3.1'

'''
    Imports
'''
import sys
import os
from functools import partial
from kivy.app import App
from kivy.core.clipboard import Clipboard, CutBuffer
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.pagelayout import PageLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty
from kivy.uix.popup import Popup
from kivy.utils import platform
from kivy.graphics import Rectangle
from kivy.metrics import dp
from Crypto.Cipher import AES
import random, struct, hashlib, pickle, logging
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
    exitText = StringProperty()
    pageText = StringProperty()
    pList = {}
    sv = ObjectProperty()
    hideNewSaveBtns = BooleanProperty(True)
    categories = ['Banking', 'Bills', 'Email', 'Shopping', 'Social Media', 'Entertainment', 'Uncategorized']

    def __init__(self, **kwargs):
        ''' standard init '''
        super(hydraView, self).__init__(**kwargs)
        self.hideNewSaveBtns = True
        self.exitText = 'Exit'
        #self.viewCatSpinner.values = self.categories

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
            else:
                #no values to load!
                logging.info('New file - nothing to load')
                self.manager.get_screen(self.manager.lastScreen).ids.loginInput.text = ''
                self.manager.get_screen(self.manager.lastScreen).ids.loginInput2.text = ''
                pass

            self.listUpdate()

        else:
            self.msgText = 'Something Went Wrong! No Manager Object'

    def pageRight(self):
        maxPage = len(self.categories)-1
        curPage = self.categories.index(self.pageText)
        if curPage < maxPage:
            self.pageText = self.categories[self.categories.index(self.pageText)+1]
            self.listUpdate(self.categories.index(self.pageText))

    def pageLeft(self):
        maxPage = len(self.categories)-1
        curPage = self.categories.index(self.pageText)
        if curPage > 0:
            self.pageText = self.categories[self.categories.index(self.pageText)-1]
            self.listUpdate(self.categories.index(self.pageText))

    def listUpdate(self,catIndex=0):
        ''' listUpdate() - Updates the password list in hydraView '''
        logging.info('Updating list of: '+str(len(self.pList)))
        viewWidth = 0.75
        delWidth = 0.25

        self.pageText = self.categories[catIndex]

        self.clean()
        if(len(self.pList.keys()) > 0):
            for site in self.pList.keys():
                if(('Category' in self.pList[site].keys() and
                    self.pList[site]['Category'] == self.categories[catIndex]) or
                    self.categories[catIndex] == 'Uncategorized' and
                    ('Category' not in self.pList[site].keys() or
                    self.pList[site]['Category'] == self.categories[catIndex])):
                    viewCallback = partial(self.viewPass, site)
                    self.passwordList.add_widget(
                        Button(text=site,
                            background_normal=os.path.join('images','pw_button.png'),
                            background_down=os.path.join('images','pw_button_down.png'),
                            on_release=viewCallback))
                    delCallback = partial(self.delPass, site)
                    self.passwordList.add_widget(
                        Button(text='Delete',
                            background_normal=os.path.join('images','pw_button.png'),
                            background_down=os.path.join('images','pw_button_down.png'),
                            on_release=delCallback))

    def copyPass(self, *args):
        if args[1] == 'name':
            logging.info('Copying Username: '+args[0])
            Clipboard.copy(self.pList[args[0]]['Username'])
        elif args[1] == 'pass':
            logging.info('Copying Password: '+args[0])
            Clipboard.copy(self.pList[args[0]]['Password'])

    def updatePass(self, site, username, password, category):
        self.pList[site] = { 'Username': username, 'Password':password, 'Category':category }
        self.listUpdate(self.categories.index(self.pageText))
        self.dismissPopup()

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
        self.listUpdate(self.categories.index(self.pageText))
        self.dismissPopup()

    def viewPass(self, *args):
        vsite = args[0]
        vpword = ''
        vuname = ''
        vcat = 'Uncategorized'
        if type(self.pList[args[0]]) is dict:
            #dict type - new format
            vuname = self.pList[args[0]]['Username']
            vpword = self.pList[args[0]]['Password']
            if 'Category' in self.pList[args[0]].keys():
                vcat = self.pList[args[0]]['Category']
            else:
                vcat = self.categories[-1] # Uncategorized
        elif type(self.pList[args[0]]) is str:
            #list type - old format
            vpword = self.pList[args[0]]
        else:
            logging.error("password list unreadable!")
        content = ViewPassDialog(site=vsite,uname=vuname,pword=vpword,cat=vcat,
                                copy=self.copyPass, save=self.updatePass, cat_options=self.categories,
                                newpass=self.showNewPass,cancel=self.dismissPopup)
        self._popup = Popup(title="View Password", content=content,
                            size_hint=(0.7,0.45))
        self._popup.open()

    def showSaveFile(self):
        content = SaveDialog(saveFile=self.saveFile,cancel=self.dismissPopup)
        self._popup = Popup(title="Save File", content=content,
                            size_hint=(0.7,0.25))
        self._popup.open()

    def newPass(self, site, category, username, pwlen, complexity):
        if(site != ''):
            self.pList[site] = { 'Username': username, 'Category':category,'Password':self.genPass(int(pwlen),complexity)}
            self.dismissPopup()
            self.listUpdate(self.categories.index(self.pageText))

    def showNewPass(self, *args):
        site = ''
        uname = ''
        cat = ''
        title='Create New Password'
        if args:
            #if we're here, we are updating an existing password
            site = args[0]
            uname = self.pList[site]['Username']
            if 'Category' in self.pList[site].keys():
                cat = self.pList[site]['Category']
            else:
                cat = 'Uncategorized'
            title='Update Password'
            #dismiss the view password popup
            self.dismissPopup()
        content = NewPassDialog(newPass=self.newPass,site_input=site,cat_input=cat,
                                uname_input=uname,cancel=self.dismissPopup,cat_options = self.categories)
        self._popup = Popup(title=title, content=content,
                            size_hint=(0.7,0.45))
        self._popup.open()

    def genPass(self, length, complexity):
        ''' genPass - generates a random password '''
        #TODO: make length/alphabet variable via setting.
        #   Note that length generally trumps complexity; this should suffice for now
        alphabet = ''
        if complexity == 'Basic [A-Za-z0-9!#&$]':
            alphabet = 'abcdefghijklmnopqrstuvwxzyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#&$'
        elif complexity == 'Full [A-Za-z0-9()[]!#&$+-,.]':
            alphabet = 'abcdefghijklmnopqrstuvwxzyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789()[]!#&$+-,.'
        elif complexity == 'Ludicrous Mode':
            #just fuck me up, fam
            asciiMax = 126
            alphabet = [chr(x) for x in range(0,asciiMax+1) if chr(x).isprintable()]
        else: # alphanumeric is the default, and has widest support (but weakest)
            alphabet = 'abcdefghijklmnopqrstuvwxzyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        pw = ''
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
            # things went well, allow all buttons
            self.hideNewSaveBtns = False
            self.exitText = 'Exit'
        except (pickle.UnpicklingError, ImportError, EOFError, IndexError, TypeError):
            logging.warning('Password incorrect or pickling failed')
            self.msgText = "Bad Password: The password you entered failed decryption, or pickling failed"
            # things didn't turn out as planned; hide the save/new buttons, update text
            self.hideNewSaveBtns = True
            self.exitText = 'Back'
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
    uname = ObjectProperty(None)
    pword = ObjectProperty(None)
    cat = ObjectProperty(None)
    cat_options = ObjectProperty(None)
    copy = ObjectProperty(None)
    newpass = ObjectProperty(None)
    save = ObjectProperty(None)
    cancel = ObjectProperty(None)

class NewPassDialog(FloatLayout):
    newPass = ObjectProperty(None)
    site_input = ObjectProperty(None)
    uname_input = ObjectProperty(None)
    cat_input = ObjectProperty(None)
    cat_options = ObjectProperty(None)
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
        self.title = 'Hydra v0.2'
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
        if platform == 'android' or platform == 'ios':
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
            Window.size = (550,700)
            try:
                #for bundling in a .exe - will fail if run as a script
                import pyi_splash
                pyi_splash.close()
            except:
                logging.info('Could not import pyi_splash...running as script?')
        else:
            self.filePathStart = '/'
            Window.size = (600,800)
            logging.info('Environment unclear?')
        self.curPlatform = platform

    def on_request_close(self, *args):
        content = SaveDialog(saveFile='',text_input='',cancel=self.dismissPopup)
        self._popup = Popup(title='Exit',content=content)
        return True



if __name__ == '__main__':
    hydraApp().run()
