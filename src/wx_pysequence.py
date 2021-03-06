#!/usr/bin/env python
# -*- coding: utf-8 -*-

##This file is part of pySequence
#############################################################################
#############################################################################
##                                                                         ##
##                               wx_pysequence                             ##
##                                                                         ##
#############################################################################
#############################################################################

## Copyright (C) 2014 Cédrick FAURY - Jean-Claude FRICOU

#    pySequence is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
    
#    pySequence is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with pySequence; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
wx_pysequence.py

pySéquence : aide à la réalisation de fiches de séquence pédagogiques
et à la validation de projets

Copyright (C) 2011-2015
@author: Cedrick FAURY

"""
####################################################################################
#
#   Import des modules nécessaires
#
####################################################################################

import time, os
import webbrowser
import version

# Chargement des images
import images

# Les objets pySequence
from Sequence import server, Sequence, Projet, Systeme, Tache, Seance, Classe

# Pour enregistrer en xml
from xml.dom.minidom import parse
import xml.etree.ElementTree as ET
Element = type(ET.Element(None))

# Module de gestion des dossiers, de l'installation et de l'enregistrement
import util_path

#####################################################################################
#   Tout ce qui concerne le GUI
#####################################################################################
import wx

# Arbre
try:
    from agw import customtreectrl as CT
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.customtreectrl as CT

try:
    from agw import hypertreelist as HTL
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.hypertreelist as HTL
    
# Gestionnaire de "pane"
import wx.aui as aui

from wx.lib.wordwrap import wordwrap
import wx.lib.hyperlink as hl
import  wx.lib.scrolledpanel as scrolled
import wx.combo
import wx.lib.platebtn as platebtn
import wx.lib.colourdb
# Pour les descriptions
import richtext

########################################################################
try:
    from agw import genericmessagedialog as GMD
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.genericmessagedialog as GMD


# Les constantes partagées
from constantes import calculerEffectifs, \
                        strEffectifComplet, getElementFiltre, \
                        CHAR_POINT, COUL_PARTIE, COUL_ABS, \
                        toFileEncoding, toSystemEncoding, FILE_ENCODING, SYSTEM_ENCODING, \
                        TOUTES_REVUES_EVAL, TOUTES_REVUES_EVAL_SOUT, TOUTES_REVUES_SOUT, TOUTES_REVUES, \
                        _S, _Rev, _R1, _R2, _R3
import constantes

# Graphiques vectoriels
import draw_cairo_seq, draw_cairo_prj, draw_cairo
try:
    import wx.lib.wxcairo
    import cairo
    haveCairo = True
except ImportError:
    haveCairo = False

# Widgets partagés
# des widgets wx évolués "faits maison"
from widgets import Variable, VariableCtrl, VAR_REEL_POS, EVT_VAR_CTRL, VAR_ENTIER_POS, \
                    messageErreur, getNomFichier, pourCent2, testRel#, chronometrer

import Options

import textwrap

import sys
if sys.platform == "win32" :
    # Pour l'enregistement dans la base de donnée Windows
    import register
    
import synthesePeda

import genpdf

from rapport import FrameRapport, RapportRTF

from math import sin, cos, pi

from Referentiel import REFERENTIELS, ARBRE_REF
import Referentiel

from operator import attrgetter


####################################################################################
#
#   Evenement perso pour détecter une modification de la séquence
#
####################################################################################
myEVT_DOC_MODIFIED = wx.NewEventType()
EVT_DOC_MODIFIED = wx.PyEventBinder(myEVT_DOC_MODIFIED, 1)

#----------------------------------------------------------------------
class SeqEvent(wx.PyCommandEvent):
    def __init__(self, evtType, idd):
        wx.PyCommandEvent.__init__(self, evtType, idd)
        self.doc = None
        self.modif = u""
        self.draw = True
        
    ######################################################################################  
    def SetDocument(self, doc):
        self.doc = doc
        
    ######################################################################################  
    def GetDocument(self):
        return self.doc
    
    ######################################################################################  
    def SetModif(self, modif):
        self.modif = modif
        
    ######################################################################################  
    def GetModif(self):
        return self.modif
    
    ######################################################################################  
    def SetDraw(self, draw):
        self.draw = draw
        
    ######################################################################################  
    def GetDraw(self):
        return self.draw


####################################################################################
#
#   Evenement perso pour signaler qu'il faut ouvrir un fichier .prj ou .seq
#   suite à un appel extérieur (explorateur Windows)
#
####################################################################################
myEVT_APPEL_OUVRIR = wx.NewEventType()
EVT_APPEL_OUVRIR = wx.PyEventBinder(myEVT_APPEL_OUVRIR, 1)

#----------------------------------------------------------------------
class AppelEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id):
        wx.PyCommandEvent.__init__(self, evtType, id)
        self.file = None
        
        
    ######################################################################################  
    def SetFile(self, fil):
        self.file = fil
        
    ######################################################################################  
    def GetFile(self):
        return self.file
    
    
def Get():
    return
####################################################################################
#
#   Quelques flags
#
####################################################################################
ALIGN_RIGHT = wx.ALIGN_RIGHT
ALL = wx.ALL
ALIGN_LEFT = wx.ALIGN_LEFT
BOTTOM = wx.BOTTOM
TOP = wx.TOP
LEFT = wx.LEFT
ICON_INFORMATION = wx.ICON_INFORMATION
ICON_WARNING = wx.ICON_WARNING
CANCEL = wx.CANCEL


####################################################################################
#
#   Quelques polices de caractères
#
####################################################################################
def getFont_9S():
    return wx.Font(9, wx.SWISS, wx.FONTSTYLE_NORMAL, wx.NORMAL, underline = True)

def getFont_9():
    return wx.Font(9, wx.SWISS, wx.FONTSTYLE_NORMAL, wx.NORMAL)



####################################################################################
#
#   Quelques icones "wx"
#
####################################################################################
def getIconeFileSave(size = (20,20)):
    return wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS, wx.ART_TOOLBAR, size)

def getIconePaste(size = (20,20)):
    return wx.ArtProvider.GetBitmap(wx.ART_PASTE, wx.ART_TOOLBAR, size)

def getIconeCopy(size = (20,20)):
    return wx.ArtProvider.GetBitmap(wx.ART_COPY, wx.ART_TOOLBAR, size)

def getIconeUndo(size = (20,20)):
    return wx.ArtProvider.GetBitmap(wx.ART_UNDO, wx.ART_TOOLBAR, size)

def getIconeRedo(size = (20,20)):
    return wx.ArtProvider.GetBitmap(wx.ART_REDO, wx.ART_TOOLBAR, size)

def getBitmapFromImageSurface(imagesurface):
    """ Renvoi une wx.Bitmap en fonction d'une cairo.ImageSurface
    """
    return wx.lib.wxcairo.BitmapFromImageSurface(imagesurface)



####################################################################################
#
#   Classes pour gérer les boutons de la Toolbar principale
#
####################################################################################
class BoutonToolBar():
    def __init__(self, label, image, shortHelp = u"", longHelp = u""):
        self.label = label
        self.image = image
        self.shortHelp = shortHelp
        self.longHelp = longHelp
#        self.fonction = fonction

####################################################################################
#
#   Classes définissant la fenétre principale de l'application
#
####################################################################################
class FenetrePrincipale(aui.AuiMDIParentFrame):
    def __init__(self, parent, fichier):
        aui.AuiMDIParentFrame.__init__(self, parent, -1, version.GetAppnameVersion(), style=wx.DEFAULT_FRAME_STYLE)
        
        self.Freeze()
        wx.lib.colourdb.updateColourDB()

        #
        # le fichier de configuration de la fiche
        #
#        self.nomFichierConfig = os.path.join(APP_DATA_PATH,"configFiche.cfg")
#        # on essaye de l'ouvrir
#        try:
#            draw_cairo_seq.ouvrirConfigFiche(self.nomFichierConfig)
#        except:
#            print "Erreur à l'ouverture de configFiche.cfg" 

        #
        # Taille et position de la fenétre
        #
        self.SetMinSize((800,570)) # Taille mini d'écran : 800x600
        self.SetSize((1024,738)) # Taille pour écran 1024x768
        # On centre la fenétre dans l'écran ...
        self.CentreOnScreen(wx.BOTH)
        
        self.SetIcon(images.getlogoIcon())
        
        self.tabmgr = self.GetClientWindow().GetAuiManager()
        self.tabmgr.GetManagedWindow().Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnDocChanged)
        
        
        #############################################################################################
        # Quelques variables ...
        #############################################################################################
        self.fichierClasse = r""
        self.pleinEcran = False
        # Element placé dans le "presse papier"
        self.elementCopie = None
        
        
        #############################################################################################
        # Création du menu
        #############################################################################################
        self.CreateMenuBar()
        
        # !!! cette ligne pose probléme à la fermeture : mystére
        self.renommerWindow()
        
        self.Bind(wx.EVT_MENU, self.commandeNouveau, id=10)
        self.Bind(wx.EVT_MENU, self.commandeOuvrir, id=11)
        self.Bind(wx.EVT_MENU, self.commandeEnregistrer, id=12)
        self.Bind(wx.EVT_MENU, self.commandeEnregistrerSous, id=13)
        self.Bind(wx.EVT_MENU, self.exporterFiche, id=15)
        self.Bind(wx.EVT_MENU, self.exporterDetails, id=16)
        self.Bind(wx.EVT_MENU_RANGE, self.OnFileHistory, id=wx.ID_FILE1, id2=wx.ID_FILE9)
        
        if sys.platform == "win32":
            self.Bind(wx.EVT_MENU, self.genererGrilles, id=17)
            self.Bind(wx.EVT_MENU, self.genererGrillesPdf, id=20)
            
        self.Bind(wx.EVT_MENU, self.genererFicheValidation, id=19)
        
        if sys.platform == "win32":
            self.Bind(wx.EVT_MENU, self.etablirBilan, id=18)
            
        self.Bind(wx.EVT_MENU, self.OnClose, id=wx.ID_EXIT)
        
        self.Bind(wx.EVT_MENU, self.OnAide, id=21)
        self.Bind(wx.EVT_MENU, self.OnAbout, id=22)
        
#        self.Bind(wx.EVT_MENU, self.OnOptions, id=31)
        
        if sys.platform == "win32" :
            self.Bind(wx.EVT_MENU, self.OnRegister, id=32)
        
        self.Bind(wx.EVT_MENU, self.OnReparer, id=33)
        
        self.Bind(EVT_APPEL_OUVRIR, self.OnAppelOuvrir)
        
        
        
        # Interception des frappes clavier
        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)
        
        # Interception de la demande de fermeture
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
        
        #############################################################################################
        # Création de la barre d'outils
        #############################################################################################
        self.ConstruireTb()
        
        
        #############################################################################################
        # Instanciation et chargement des options
        #############################################################################################
        options = Options.Options()
        if options.fichierExiste():
#            options.ouvrir(DEFAUT_ENCODING)
            try :
                options.ouvrir(SYSTEM_ENCODING)
            except:
                print "Fichier d'options corrompus ou inexistant !! Initialisation ..."
                options.defaut()
        else:
            options.defaut()
        self.options = options
#        print options
        
        # On applique les options ...
        self.DefinirOptions(options)
        
#        #################################################################################################################
#        #
#        # Mise en place
#        #
#        #################################################################################################################
#        sizer = wx.BoxSizer(wx.VERTICAL)
#        sizer.Add(sizerTb, 0, wx.EXPAND)
#        sizer.Add(self.fenDoc, 0, wx.EXPAND)
#        self.SetSizer(sizer)
        
        if fichier != "":
            self.ouvrir(fichier)


        # Récupération de la derniére version
        import threading 
        a = threading.Thread(None, version.GetNewVersion, None,  (self,) )
        a.start()

        self.Thaw()
        
    
    def renommerWindow(self):
        menu_bar = self.GetMenuBar()
#        menu_bar.SetMenuLabel(3, u"Fenétre")
#        menu_bar.SetMenuLabel(menu_bar.FindMenu("Window"), u"Fenétre")
        
    
    ###############################################################################################
    def SetData(self, data):  
        self.elementCopie = data      
        
    ###############################################################################################
    def GetTools(self, typ):
        if typ == 'prj':
            return {50 : BoutonToolBar(u"Ajouter un élève",
                                   images.Icone_ajout_eleve.GetBitmap(), 
                                   shortHelp = u"Ajout d'un élève au projet", 
                                   longHelp = u"Ajout d'un élève au projet"),
                
                    51 : BoutonToolBar(u"Ajouter un professeur", 
                                       images.Icone_ajout_prof.GetBitmap(), 
                                       shortHelp = u"Ajout d'un professeur à l'équipe pédagogique", 
                                       longHelp = u"Ajout d'un professeur à l'équipe pédagogique"),
                    
                    52 : BoutonToolBar(u"Ajouter une tâche", 
                                       images.Icone_ajout_tache.GetBitmap(), 
                                       shortHelp=u"Ajout d'une tâche au projet", 
                                       longHelp=u"Ajout d'une tâche au projet"),
                    
                    53 : BoutonToolBar(u"Ajouter une revue", 
                                       images.Icone_ajout_revue.GetBitmap(), 
                                       shortHelp = u"Ajout d'une revue au projet", 
                                       longHelp = u"Ajout d'une revue au projet")
                }
        
        elif typ == 'seq':
            return {60 : BoutonToolBar(u"Ajouter une séance", 
                                    images.Icone_ajout_seance.GetBitmap(), 
                                    shortHelp=u"Ajout d'une séance dans la séquence", 
                                    longHelp=u"Ajout d'une séance dans la séquence"),

                  61 : BoutonToolBar(u"Ajouter un système", 
                                     images.Icone_ajout_systeme.GetBitmap(), 
                                     shortHelp=u"Ajout d'un système", 
                                     longHelp=u"Ajout d'un système")
                  }
            
            
            
    ###############################################################################################
    def ConstruireTb(self):
        """ Construction de la ToolBar
        """
#        print "ConstruireTb"

        #############################################################################################
        # Création de la barre d'outils
        #############################################################################################
        self.tb = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        
        
        tsize = (24,24)
        new_bmp =  wx.ArtProvider.GetBitmap(wx.ART_NEW, wx.ART_TOOLBAR, tsize)
        open_bmp = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR, tsize)
        save_bmp =  wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR, tsize)
        saveas_bmp = wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS, wx.ART_TOOLBAR, tsize)
        undo_bmp = wx.ArtProvider.GetBitmap(wx.ART_UNDO, wx.ART_TOOLBAR, tsize)
        redo_bmp = wx.ArtProvider.GetBitmap(wx.ART_REDO, wx.ART_TOOLBAR, tsize)
        
        self.tb.SetToolBitmapSize(tsize)
        
        self.tb.AddLabelTool(10, u"Nouveau", new_bmp, 
                             shortHelp=u"Création d'une nouvelle séquence ou d'un nouveau projet", 
                             longHelp=u"Création d'une nouvelle séquence ou d'un nouveau projet")
        

        self.tb.AddLabelTool(11, u"Ouvrir", open_bmp, 
                             shortHelp=u"Ouverture d'un fichier séquence ou projet", 
                             longHelp=u"Ouverture d'un fichier séquence ou projet")
        
        self.tb.AddLabelTool(12, u"Enregistrer", save_bmp, 
                             shortHelp=u"Enregistrement du document courant sous son nom actuel", 
                             longHelp=u"Enregistrement du document courant sous son nom actuel")
        

        self.tb.AddLabelTool(13, u"Enregistrer sous...", saveas_bmp, 
                             shortHelp=u"Enregistrement du document courant sous un nom différent", 
                             longHelp=u"Enregistrement du document courant sous un nom différent")
        
        self.Bind(wx.EVT_TOOL, self.commandeNouveau, id=10)
        self.Bind(wx.EVT_TOOL, self.commandeOuvrir, id=11)
        self.Bind(wx.EVT_TOOL, self.commandeEnregistrer, id=12)
        self.Bind(wx.EVT_TOOL, self.commandeEnregistrerSous, id=13)
        
        
        self.tb.AddSeparator()
        
        self.tb.AddLabelTool(200, u"Annuler", undo_bmp, 
                             shortHelp=u"Annuler", 
                             longHelp=u"Annuler")
        

        self.tb.AddLabelTool(201, u"Rétablir", redo_bmp, 
                             shortHelp=u"Rétablir", 
                             longHelp=u"Rétablir")
        
        
        self.tb.AddSeparator()
        
        self.Bind(wx.EVT_TOOL, self.commandeUndo, id=200)
        self.Bind(wx.EVT_TOOL, self.commandeRedo, id=201)
        
        
        #################################################################################################################
        #
        # Outils "Projet" ou  "séquence" ou ...
        #
        #################################################################################################################
        self.tools = {'prj' : {}, 'seq' : {}}
        for typ in ['prj', 'seq']:
            for i, tool in self.GetTools(typ).items():
                self.tools[typ][i] = self.tb.AddLabelTool(i, tool.label, tool.image, 
                                                           shortHelp = tool.shortHelp, 
                                                           longHelp = tool.longHelp)

        

        self.tb.AddSeparator()
        #################################################################################################################
        #
        # Outils de Visualisation
        #
        #################################################################################################################
        saveas_bmp = images.Icone_fullscreen.GetBitmap()
        self.tb.AddLabelTool(100, u"Plein écran", saveas_bmp, 
                             shortHelp=u"Affichage de la fiche en plein écran (Echap pour quitter le mode plein écran)", 
                             longHelp=u"Affichage de la fiche en plein écran (Echap pour quitter le mode plein écran)")

        self.Bind(wx.EVT_TOOL, self.commandePleinEcran, id=100)
        
        
#        self.Bind(wx.EVT_TOOL, self.OnClose, id=wx.ID_EXIT)
#        
#        self.Bind(wx.EVT_TOOL, self.OnAide, id=21)
#        self.Bind(wx.EVT_TOOL, self.OnAbout, id=22)
#        
#        self.Bind(wx.EVT_TOOL, self.OnOptions, id=31)
#        self.Bind(wx.EVT_TOOL, self.OnRegister, id=32)
        
        self.tb.AddSeparator()
        
        
        
        #################################################################################################################
        #
        # Mise en place
        #
        #################################################################################################################
        self.tb.Realize()
        self.supprimerOutils()
        self.miseAJourUndo()
        
        
        
    ###############################################################################################
    def supprimerOutils(self):
        self.tb.RemoveTool(60)
        self.tb.RemoveTool(61)
        self.tb.RemoveTool(50)
        self.tb.RemoveTool(51)
        self.tb.RemoveTool(52)
        self.tb.RemoveTool(53)


    ###############################################################################################
    def ajouterOutils(self, typ):
        self.supprimerOutils()

        d = 8 # Position à changer selon le nombre d'outils "communs"
        for i, tool in self.tools[typ].items():
            self.tb.InsertToolItem(d,tool)
            d += 1
        
        
        self.tb.Realize()


    ###############################################################################################
    def miseAJourUndo(self):
        """ Mise à jour des boutons (et menus)
            après une opération undo ou redo
        """
        try:
            doc = self.GetDocActif()
        except:
            doc = None
        if doc == None:
            self.tb.EnableTool(200, False)
            self.tb.EnableTool(201, False)
            return
            
        undoAction = doc.undoStack.getUndoAction()
        if undoAction == None:
            self.tb.EnableTool(200, False)
            t = u""
        else:
            self.tb.EnableTool(200, True)
            t = u"\n"+undoAction
        self.tb.SetToolShortHelp(200, u"Annuler"+t)

        redoAction = doc.undoStack.getRedoAction()
        if redoAction == None:
            self.tb.EnableTool(201, False)
            t = u""
        else:
            self.tb.EnableTool(201, True)
            u"\n"+redoAction
        self.tb.SetToolShortHelp(201, u"Rétablir"+t)
        
        
    ###############################################################################################
    def commandePleinEcran(self, event):
        if self.GetNotebook().GetCurrentPage() == None:
            return
        
        self.pleinEcran = not self.pleinEcran
        
        if self.pleinEcran:
            win = self.GetNotebook().GetCurrentPage().nb.GetCurrentPage()
            self.fsframe = wx.Frame(self, -1)
            win.Reparent(self.fsframe)
            win.Bind(wx.EVT_KEY_DOWN, self.OnKey)
            self.fsframe.ShowFullScreen(True, style=wx.FULLSCREEN_ALL)
            
        else:
            win = self.fsframe.GetChildren()[0]
            win.Reparent(self.GetNotebook().GetCurrentPage().nb)
            self.fsframe.Destroy()
            win.SendSizeEventToParent()


    ###############################################################################################
    def CreateMenuBar(self):
        # create menu
        
        window_menu = self.GetWindowMenu()
        window_menu.SetLabel(4001, u"Fermer")
        window_menu.SetLabel(4002, u"Fermer tout")
        window_menu.SetLabel(4003, u"Suivante")
        window_menu.SetLabel(4004, u"Précédente")
        
        mb = wx.MenuBar()

        file_menu = wx.Menu()
        file_menu.Append(10, u"&Nouveau\tCtrl+N")
        file_menu.Append(11, u"&Ouvrir\tCtrl+O")
        
        submenu = wx.Menu()
        file_menu.AppendMenu(14, u"&Ouvrir un fichier récent", submenu)
        self.filehistory = wx.FileHistory()
        self.filehistory.UseMenu(submenu)
        
        file_menu.Append(12, u"&Enregistrer\tCtrl+S")
        file_menu.Append(13, u"&Enregistrer sous ...")
        file_menu.AppendSeparator()
        
#        file_menu.AppendSeparator()
        file_menu.Append(15, u"&Exporter la fiche (PDF ou SVG)\tCtrl+E")
        file_menu.Append(16, u"&Exporter les détails\tCtrl+D")
        
        if sys.platform == "win32":
            file_menu.Append(17, u"&Générer les grilles d'évaluation projet\tCtrl+G")
            file_menu.Append(20, u"&Générer les grilles d'évaluation projet en PDF\tCtrl+P")
        
        file_menu.Append(19, u"&Générer le dossier de validation projet\tAlt+V")
        
        if sys.platform == "win32":
            file_menu.Append(18, u"&Générer une Synthése pédagogique\tCtrl+B")
        
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, u"&Quitter\tCtrl+Q")

        self.file_menu = file_menu
        
        tool_menu = wx.Menu()
        
        if sys.platform == "win32" and util_path.INSTALL_PATH != None:
    #        tool_menu.Append(31, u"Options")
            self.menuReg = tool_menu.Append(32, u"a")
            self.MiseAJourMenu()
        self.menuRep = tool_menu.Append(33, u"Ouvrir et réparer un fichier")

        help_menu = wx.Menu()
        help_menu.Append(21, u"&Aide en ligne\tF1")
        help_menu.AppendSeparator()
        help_menu.Append(22, u"A propos")

        mb.Append(file_menu, u"&Fichier")
        mb.Append(tool_menu, u"&Outils")
        mb.Append(help_menu, u"&Aide")
        
        self.SetMenuBar(mb)
    
    
    #############################################################################
    def MiseAJourMenu(self):
        if hasattr(self, 'menuReg'):
            if register.IsRegistered():
                self.menuReg.SetText(u"Désinscrire de la base de registre")
            else:
                self.menuReg.SetText(u"Inscrire dans la base de registre")
            
            
            
    #############################################################################
    def DefinirOptions(self, options):
        for f in reversed(options.optFichiers["FichiersRecents"]):
            self.filehistory.AddFileToHistory(f)
            
#        self.options = options.copie()
#        #
#        # Options de Classe
#        #
#        
##        te = self.options.optClasse["TypeEnseignement"]
#        lstCI = self.options.optClasse["CentresInteretET"]
#        if False:
#            pass
##        if self.fichierCourantModifie and (te != TYPE_ENSEIGNEMENT \
##           or (te == 'ET' and getTextCI(CentresInterets[TYPE_ENSEIGNEMENT]) != lstCI)):
##            dlg = wx.MessageDialog(self, u"Type de classe incompatible !\n\n" \
##                                         u"Fermer la séquence en cours d'élaboration\n" \
##                                         u"avant de modifier des options de la classe.",
##                               'Type de classe incompatible',
##                               wx.OK | wx.ICON_INFORMATION
##                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
##                               )
##            dlg.ShowModal()
##            dlg.Destroy()
#        else:
##            TYPE_ENSEIGNEMENT = te
#
#            constantes.Effectifs["C"] = self.options.optClasse["Effectifs"]["C"]
#            constantes.NbrGroupes["G"] = self.options.optClasse["Effectifs"]["G"]
#            constantes.NbrGroupes["E"] = self.options.optClasse["Effectifs"]["E"]
#            constantes.NbrGroupes["P"] = self.options.optClasse["Effectifs"]["P"]
#                          
#            constantes.CentresInteretsET = lstCI
#                
#            constantes.PositionCibleCIET = self.options.optClasse["PositionsCI_ET"]
    
    #############################################################################
    def OnReparer(self, event):
        dlg = wx.MessageDialog(self, u"Ouvrir et réparer un fichier de projet\n\n" \
                               u"L'opération qui va suivre permet d'ouvrir un fichier de projet (.prj)\n" \
                               u"en restaurant les valeurs par défaut du programme d'enseignement.\n" \
                               u"Si le projet utilise un programme d'enseignement personnalisé,\n" \
                               u"les spécificités de ce dernier seront perdues.\n\n"\
                               u"Voulez-vous continuer ?",
                                 u"Ouvrir et réparer",
                                 wx.ICON_INFORMATION | wx.YES_NO | wx.CANCEL
                                 )
        res = dlg.ShowModal()
        dlg.Destroy() 
        if res == wx.ID_YES:
            self.commandeOuvrir(reparer = True)
            

         
                
    #############################################################################
    def OnRegister(self, event): 
        if register.IsRegistered():
            ok = register.UnRegister()
        else:
            ok = register.Register(util_path.PATH)
        if not ok:
            messageErreur(self, u"Accés refusé",
                          u"Accés à la base de registre refusé !\n\n" \
                          u"Redémarrer pySequence en tant qu'administrateur.")
        else:
            self.MiseAJourMenu()
         
    #############################################################################
    def OnAbout(self, event):
        win = A_propos(self)
        win.ShowModal()
        
    #############################################################################
    def OnAide(self, event):
        try:
            webbrowser.open('https://github.com/cedrick-f/pySequence/wiki',new=2)
        except:
            messageErreur(None, u"Ouverture impossible",
                          u"Impossible d'ouvrir l'url\n\n%s\n" %toSystemEncoding(self.path))

        
        
    ###############################################################################################
    def commandeNouveau(self, event = None, ext = None, ouverture = False):
#        print "commandeNouveau"
        if ext == None:
            dlg = DialogChoixDoc(self)
            val = dlg.ShowModal()
            dlg.Destroy()
            if val == 1:
                ext = 'seq' 
            elif val == 2:
                ext = 'prj'
            else:
                return
                
        if ext == 'seq':
            child = FenetreSequence(self, ouverture)
        elif ext == 'prj':
            child = FenetreProjet(self)
        
        self.OnDocChanged(None)
        if child != None:
            wx.CallAfter(child.Activate)
        return child


    ###############################################################################################
    def ouvrir(self, nomFichier, reparer = False):
        self.Freeze()
        wx.BeginBusyCursor()
        
        if nomFichier != '':
            ext = os.path.splitext(nomFichier)[1].lstrip('.')
            
            # Fichier pas déja ouvert
            if not nomFichier in self.GetNomsFichiers():
                
                child = self.commandeNouveau(ext = ext, ouverture = True)
                if child != None:
                    child.ouvrir(nomFichier, reparer = reparer)
                
            # Fichier déja ouvert
            else:
                child = self.GetChild(nomFichier)
                texte = constantes.MESSAGE_DEJA[ext] % child.fichierCourant
#                if child.fichierCourant != '':
#                    texte += "\n\n\t"+child.fichierCourant+"\n"
                    
                dialog = wx.MessageDialog(self, texte, 
                                          u"Confirmation", wx.YES_NO | wx.ICON_WARNING)
                retCode = dialog.ShowModal()
                if retCode == wx.ID_YES:
                    child.ouvrir(nomFichier, reparer = reparer)
            
            if not reparer:
                self.filehistory.AddFileToHistory(nomFichier)
            
        wx.EndBusyCursor()
        self.Thaw()


    ###############################################################################################
    def commandeOuvrir(self, event = None, nomFichier = None, reparer = False):
        mesFormats = constantes.FORMAT_FICHIER['seqprj'] + constantes.FORMAT_FICHIER['seq'] + constantes.FORMAT_FICHIER['prj'] + constantes.TOUS_FICHIER
  
        if nomFichier == None:
            dlg = wx.FileDialog(
                                self, message=u"Ouvrir une séquence ou un projet",
#                                defaultDir = self.DossierSauvegarde, 
                                defaultFile = "",
                                wildcard = mesFormats,
                                style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
                                )

            if dlg.ShowModal() == wx.ID_OK:
                paths = dlg.GetPaths()
                nomFichier = paths[0]
            else:
                nomFichier = ''
            
            dlg.Destroy()
        
        
            
        self.ouvrir(nomFichier, reparer = reparer)
        
        
    ###############################################################################################
    def OnFileHistory(self, evt):
        # get the file based on the menu ID
        fileNum = evt.GetId() - wx.ID_FILE1
        path = self.filehistory.GetHistoryFile(fileNum)
#        print "You selected %s\n" % path

        # add it back to the history so it will be moved up the list
        self.filehistory.AddFileToHistory(path)
        self.commandeOuvrir(nomFichier = path)


    ###############################################################################################
    def GetFichiersRecents(self):
        lst = []
        for n in range(self.filehistory.GetCount()):
            lst.append(self.filehistory.GetHistoryFile(n))
        return lst


    ###############################################################################################
    def OnAppelOuvrir(self, evt):
#        print "OnAppelOuvrir"
        wx.CallAfter(self.ouvrir, evt.GetFile())
        
        
    ###############################################################################################
    def AppelOuvrir(self, nomFichier):
        evt = AppelEvent(myEVT_APPEL_OUVRIR, self.GetId())
        evt.SetFile(nomFichier)
        self.GetEventHandler().ProcessEvent(evt)
        
    #############################################################################
    def commandeUndo(self, event = None):
        page = self.GetNotebook().GetCurrentPage()
        if page != None:
            page.commandeUndo(event)
    
    #############################################################################
    def commandeRedo(self, event = None):
        page = self.GetNotebook().GetCurrentPage()
        if page != None:
            page.commandeRedo(event)     
            
    #############################################################################
    def commandeEnregistrer(self, event = None):
        page = self.GetNotebook().GetCurrentPage()
        if page != None:
            page.commandeEnregistrer(event)
        
    #############################################################################
    def commandeEnregistrerSous(self, event = None):
        page = self.GetNotebook().GetCurrentPage()
        if page != None:
            page.commandeEnregistrerSous(event)
    
    #############################################################################
    def exporterFiche(self, event = None):
        page = self.GetNotebook().GetCurrentPage()
        if page != None:
            page.exporterFiche(event)
              
    #############################################################################
    def exporterDetails(self, event = None):
        page = self.GetNotebook().GetCurrentPage()
        if page != None:
            page.exporterDetails(event)
        
    #############################################################################
    def genererGrilles(self, event = None):
        page = self.GetNotebook().GetCurrentPage()
        if page != None:
            page.genererGrilles(event)
            
            
    #############################################################################
    def genererGrillesPdf(self, event = None):
        page = self.GetNotebook().GetCurrentPage()
        if page != None:
            page.genererGrillesPdf(event)
            
    #############################################################################
    def genererFicheValidation(self, event = None):
        page = self.GetNotebook().GetCurrentPage()
        if page != None:
            page.genererFicheValidation(event)
    
    #############################################################################
    def etablirBilan(self, event = None):
        for w in self.GetChildren():
            if isinstance(w, synthesePeda.FenetreBilan):
                w.SetFocus()
                return
#        if self.GetFenetreActive() != None:
        if self.GetFenetreActive():
            dossier = self.GetFenetreActive().DossierSauvegarde
            if isinstance(self.GetFenetreActive(), FenetreSequence):
                ref = self.GetFenetreActive().sequence.GetReferentiel()
            else:
                ref = None
        else:
            dossier = util_path.INSTALL_PATH
            ref = None
        win = synthesePeda.FenetreBilan(self, dossier, ref)
        win.Show()
#        win.Destroy()
        
        
        
#    #############################################################################
#    def OnOptions(self, event, page = 0):
#        options = self.options.copie()
#        dlg = Options.FenOptions(self, options)
#        dlg.CenterOnScreen()
#        dlg.nb.SetSelection(page)
#
#        # this does not return until the dialog is closed.
#        val = dlg.ShowModal()
#    
#        if val == wx.ID_OK:
#            self.DefinirOptions(options)
#            self.AppliquerOptions()
#            
#        else:
#            pass
#
#        dlg.Destroy()
            
        
    ###############################################################################################
    def OnDocChanged(self, evt):
        """ Opérations de modification du menu et des barres d'outils 
            en fonction du type de document en cours
        """
        fenDoc = self.GetClientWindow().GetAuiManager().GetManagedWindow().GetCurrentPage()
        if hasattr(fenDoc, 'typ'):
            self.ajouterOutils(fenDoc.typ )
            if fenDoc.typ == "prj":
                self.Bind(wx.EVT_TOOL, fenDoc.projet.AjouterEleve, id=50)
                self.Bind(wx.EVT_TOOL, fenDoc.projet.AjouterProf, id=51)
                self.Bind(wx.EVT_TOOL, fenDoc.AjouterTache, id=52)
                self.Bind(wx.EVT_TOOL, fenDoc.projet.InsererRevue, id=53)
                
            elif fenDoc.typ == "seq":
                self.Bind(wx.EVT_TOOL, fenDoc.sequence.AjouterSeance, id=60)
                self.Bind(wx.EVT_TOOL, fenDoc.sequence.AjouterSysteme, id=61)
    
            if fenDoc.typ == "prj":
                self.file_menu.Enable(18, True)
                self.file_menu.Enable(17, True)
                self.file_menu.Enable(19, True)
                self.file_menu.Enable(20, True)
                
            elif fenDoc.typ == "seq":
                self.file_menu.Enable(18, True)
                self.file_menu.Enable(17, False)
                self.file_menu.Enable(19, False)
                self.file_menu.Enable(20, False)
                
        self.miseAJourUndo()
           
        
    ###############################################################################################
    def OnKey(self, evt):
        keycode = evt.GetKeyCode()
        if keycode == wx.WXK_ESCAPE and self.pleinEcran:
            self.commandePleinEcran(evt)
            
        elif evt.ControlDown() and keycode == 90: # Crtl-Z
            self.commandeUndo(evt)


        elif evt.ControlDown() and keycode == 89: # Crtl-Y
            self.commandeRedo(evt)
            
        evt.Skip()
        
        
#    ###############################################################################################
#    def OnToolClick(self, event):
#        self.log.WriteText("tool %s clicked\n" % event.GetId())
#        #tb = self.GetToolBar()
#        tb = event.GetEventObject()
#        tb.EnableTool(10, not tb.GetToolEnabled(10))
 
        
    
    
                
    #############################################################################
    def GetChild(self, nomFichier):
        for m in self.GetChildren():
            if isinstance(m, aui.AuiMDIClientWindow):
                for k in m.GetChildren():
                    if isinstance(k, FenetreSequence):
                        if k.fichierCourant == nomFichier:
                            return k
        return
    
    
    #############################################################################
    def GetDocActif(self):
        if self.GetNotebook() != None and self.GetNotebook().GetCurrentPage() != None:
            return self.GetNotebook().GetCurrentPage().GetDocument()
    
    #############################################################################
    def GetFenetreActive(self):
        return self.GetNotebook().GetCurrentPage()
    
    #############################################################################
    def GetNomsFichiers(self):
        lst = []
        for m in self.GetChildren():
            if isinstance(m, aui.AuiMDIClientWindow):
                for k in m.GetChildren():
                    if isinstance(k, FenetreSequence):
                        lst.append(k.fichierCourant)

        return lst
    
    
    
    
    #############################################################################
    def OnClose(self, evt):
#        print "OnClose"
#        try:
#            draw_cairo.enregistrerConfigFiche(self.nomFichierConfig)
#        except IOError:
#            print "   Permission d'enregistrer les options refusée...",
#        except:
#            print "   Erreur enregistrement options...",
            
        try:
            self.options.definir()
            self.options.valider(self)
            self.options.enregistrer()
        except IOError:
            print "   Permission d'enregistrer les options refusée...",
        except:
            print "   Erreur enregistrement options...",
#        
        
        
        # Close all ChildFrames first else Python crashes
        toutferme = True
        for m in self.GetChildren():
            if isinstance(m, aui.AuiMDIClientWindow):
                for k in m.GetChildren():
                    if isinstance(k, FenetreDocument):
                        toutferme = toutferme and k.quitter()  
        
#        print ">>", toutferme
        if toutferme:
            evt.Skip()
            sys.exit()
#            self.Destroy()

        
        
########################################################################################
#
#
#  Classe définissant la fenétre "Document" (séquence, projet, ...)
#     qui apparait en onglet
#
#
########################################################################################
class FenetreDocument(aui.AuiMDIChildFrame):
    def __init__(self, parent):
        
        aui.AuiMDIChildFrame.__init__(self, parent, -1, "")#, style = wx.DEFAULT_FRAME_STYLE | wx.SYSTEM_MENU)
#        self.SetExtraStyle(wx.FRAME_EX_CONTEXTHELP)
        
        self.parent = parent
        
        # Use a panel under the AUI panes in order to work around a
        # bug on PPC Macs
        pnl = wx.Panel(self)
        self.pnl = pnl
        
        self.mgr = aui.AuiManager()
        self.mgr.SetManagedWindow(pnl)
        
        # panel de propriétés (conteneur)
        self.panelProp = PanelConteneur(pnl)
        
        #
        # Pour la sauvegarde
        #
        self.fichierCourant = u""
        self.DossierSauvegarde = u""
        self.fichierCourantModifie = False
            
        #
        # Un NoteBook comme conteneur de la fiche
        #
        self.nb = wx.Notebook(self.pnl, -1)
        
        
        
        
        
    def miseEnPlace(self):
        
        #############################################################################################
        # Mise en place de la zone graphique
        #############################################################################################
        self.mgr.AddPane(self.nb, 
                         aui.AuiPaneInfo().
                         CenterPane()
#                         Caption(u"Bode").
#                         PaneBorder(False).
#                         Floatable(False).
#                         CloseButton(False)
#                         Name("Bode")
#                         Layer(2).BestSize(self.zoneGraph.GetMaxSize()).
#                         MaxSize(self.zoneGraph.GetMaxSize())
                        )
        
        #############################################################################################
        # Mise en place de l'arbre
        #############################################################################################
        self.mgr.AddPane(self.arbre, 
                         aui.AuiPaneInfo().
#                         Name(u"Structure").
                         Left().Layer(1).
                         Floatable(False).
                         BestSize((250, -1)).
                         MinSize((250, -1)).
#                         DockFixed().
#                         Gripper(False).
#                         Movable(False).
                         Maximize().
                         Caption(u"Structure").
                         CaptionVisible(True).
#                         PaneBorder(False).
                         CloseButton(False)
#                         Show()
                         )
        
        #############################################################################################
        # Mise en place du panel de propriétés
        #############################################################################################
        self.mgr.AddPane(self.panelProp, 
                         aui.AuiPaneInfo().
#                         Name(u"Structure").
                         Bottom().
                         Layer(1).
#                         Floatable(False).
                         BestSize((600, 200)).
                         MinSize((600, 200)).
                         MinimizeButton(True).
                         Resizable(True).

#                         DockFixed().
#                         Gripper(True).
#                         Movable(False).
#                         Maximize().
                         Caption(u"Propriétés").
                         CaptionVisible(True).
#                         PaneBorder(False).
                         CloseButton(False)
#                         Show()
                         )
        

        self.mgr.Update()

        self.definirNomFichierCourant('')
    
        sizer = wx.BoxSizer()
        sizer.Add(self.pnl, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        self.Layout()
        
        self.Bind(EVT_DOC_MODIFIED, self.OnDocModified)
        self.Bind(wx.EVT_CLOSE, self.quitter)
        

    #############################################################################
    def fermer(self):
        self.mgr.UnInit()
        del self.mgr
        self.Destroy()
        return True
        
    #############################################################################
    def getNomFichierCourantCourt(self):
        return os.path.splitext(os.path.split(self.fichierCourant)[-1])[0]
    
    #############################################################################
    def MarquerFichierCourantModifie(self, modif = True):
        self.fichierCourantModifie = modif
        self.SetTitre(modif)

        
    #############################################################################
    def AfficherMenuContextuel(self, items):
        """ Affiche un menu contextuel contenant les items spécifiés
                items = [ [nom1, fct1], [nom2, fct2], ...]
        """
        menu = wx.Menu()
        
        for nom, fct, img in items:
            item = wx.MenuItem(menu, wx.ID_ANY, nom)
            if img != None:
                item.SetBitmap(img)
            item1 = menu.AppendItem(item)    
            self.Bind(wx.EVT_MENU, fct, item1)
        
        self.PopupMenu(menu)
        menu.Destroy()
    
    #############################################################################
    def dialogEnregistrer(self):
        mesFormats = constantes.FORMAT_FICHIER[self.typ] + constantes.TOUS_FICHIER
        dlg = wx.FileDialog(self, 
                            message = constantes.MESSAGE_ENR[self.typ], 
                            defaultDir=toSystemEncoding(self.DossierSauvegarde) , # encodage?
                            defaultFile="", wildcard=mesFormats, 
                            style=wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR
                            )
        dlg.SetFilterIndex(0)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            dlg.Destroy()
            self.enregistrer(path)
            self.DossierSauvegarde = os.path.split(path)[0]
        else:
            dlg.Destroy()
    
    
    #############################################################################
    def commandeRedo(self, event = None):
        self.GetDocument().undoStack.redo()
        self.GetDocument().classe.undoStack.redo()
        wx.BeginBusyCursor()
        self.restaurer()
        wx.EndBusyCursor()
        
    #############################################################################
    def commandeUndo(self, event = None):
        t0 = time.time()
        self.GetDocument().undoStack.undo()
        t1 = time.time()
        print "  ", t1-t0
        
        self.GetDocument().classe.undoStack.undo()
        t2 = time.time()
        print "  ", t2-t1
        
        wx.BeginBusyCursor()
        self.restaurer()
        wx.EndBusyCursor()
    
    #############################################################################
    def commandeEnregistrer(self, event = None):
        if self.fichierCourant != '':
            self.enregistrer(self.fichierCourant)
        else:
            self.dialogEnregistrer()        
            
    #############################################################################
    def commandeEnregistrerSous(self, event = None):
        self.dialogEnregistrer()
    
    #############################################################################
    def SetTitre(self, modif = False):
        t = self.classe.typeEnseignement
        t = REFERENTIELS[t].Enseignement[0]
        if self.fichierCourant == '':
            t += u" - "+constantes.TITRE_DEFAUT[self.typ]
        else:
            t += u" - "+os.path.splitext(os.path.basename(self.fichierCourant))[0]
        if modif :
            t += " **"
        self.SetTitle(t)#toSystemEncoding(t))
        
    #############################################################################
    def exporterFichePDF(self, nomFichier, pourDossierValidation = False):
        try:
            PDFsurface = cairo.PDFSurface(nomFichier, 595, 842)
        except IOError:
            Dialog_ErreurAccesFichier(nomFichier)
            wx.EndBusyCursor()
            return
        
        ctx = cairo.Context(PDFsurface)
        ctx.scale(820, 820) 
        if self.typ == 'seq':
            draw_cairo_seq.Draw(ctx, self.sequence)
        elif self.typ == 'prj':
            draw_cairo_prj.Draw(ctx, self.projet, pourDossierValidation = pourDossierValidation)
        
        PDFsurface.finish()
        
    
    #############################################################################
    def exporterFiche(self, event = None):
        mesFormats = "pdf (.pdf)|*.pdf|" \
                     "svg (.svg)|*.svg"
#                     "swf (.swf)|*.swf"
        dlg = wx.FileDialog(
            self, message=u"Enregistrer la fiche sous ...", defaultDir=toSystemEncoding(self.DossierSauvegarde) , 
            defaultFile = os.path.splitext(self.fichierCourant)[0]+".pdf", 
            wildcard=mesFormats, style=wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR
            )
        dlg.SetFilterIndex(0)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()#.encode(FILE_ENCODING)
            ext = os.path.splitext(path)[1]
            dlg.Destroy()
            wx.BeginBusyCursor()
            if ext == ".pdf":
                self.exporterFichePDF(path)
                self.DossierSauvegarde = os.path.split(path)[0]
                os.startfile(path)
            elif ext == ".svg":
                try:
                    SVGsurface = cairo.SVGSurface(path, 595, 842)
                except IOError:
                    Dialog_ErreurAccesFichier(path)
                    wx.EndBusyCursor()
                    return
                
                ctx = cairo.Context (SVGsurface)
                ctx.scale(820, 820) 
                if self.typ == 'seq':
                    draw_cairo_seq.Draw(ctx, self.sequence, mouchard = True)
                elif self.typ == 'prj':
                    draw_cairo_prj.Draw(ctx, self.projet)
                self.DossierSauvegarde = os.path.split(path)[0]
                SVGsurface.finish()
                self.enrichirSVG(path)
            wx.EndBusyCursor()

#                os.startfile(path)
#            elif ext == ".swf":
#                fichierTempo = tempfile.NamedTemporaryFile(delete=False)
#                SVGsurface = cairo.SVGSurface(fichierTempo, 595, 842)
#                ctx = cairo.Context (SVGsurface)
#                ctx.scale(820, 820) 
#                draw_cairo.Draw(ctx, self.sequence)
#                self.DossierSauvegarde = os.path.split(path)[0]
#                SVGsurface.finish()
#                svg_export.saveSWF(fichierTempo, path)
        else:
            dlg.Destroy()
        return
    
    
    #############################################################################
    def exporterDetails(self, event = None):
        if hasattr(self, 'projet'):
            win = FrameRapport(self, self.fichierCourant, self.projet, 'prj')
            win.Show()
        elif hasattr(self, 'sequence'):
            win = FrameRapport(self, self.fichierCourant, self.sequence, 'seq')
            win.Show()
#            win.Destroy()

    #############################################################################
    def genererGrilles(self, event = None):
        return
    
    #############################################################################
    def genererFicheValidation(self, event = None):
        return
    
    #############################################################################
    def quitter(self, event = None):
        if self.fichierCourantModifie:
            texte = constantes.MESSAGE_FERMER[self.typ] % self.fichierCourant
#            if self.fichierCourant != '':
#                texte += "\n\n\t"+self.fichierCourant+"\n"
                
            dialog = wx.MessageDialog(self, texte, 
                                      u"Confirmation", wx.YES_NO | wx.CANCEL | wx.ICON_WARNING)
            retCode = dialog.ShowModal()
            if retCode == wx.ID_YES:
                self.commandeEnregistrer()
                return self.fermer()
    
            elif retCode == wx.ID_NO:
                
                return self.fermer()
                 
            else:
                return False
        
        else:            
            
            return self.fermer()


    #############################################################################
    def enrichirSVG(self, path):
        """ Enrichissement de l'image SVG <path> avec :
             - mise en surbrillance des éléments actifs
             - infobulles sur les éléments actifs
             - liens 
             - ...
        """
        epsilon = 0.001

        doc = parse(path)
        
        f = open(path, 'w')

        defs = doc.getElementsByTagName("defs")[0]
        defs.appendChild(getElementFiltre(constantes.FILTRE1))
        
        def match(p0, p1):
            return abs(p0[0]-p1[0])<epsilon and abs(p0[1]-p1[1])<epsilon
        
        # Récupération des points caractéristiques sur la fiche
        pts_caract = self.GetDocument().GetPtCaract()
#        if self.typ == 'seq':
#            pts_caract = self.sequence.GetPtCaract()
#        else:
#            pts_caract = self.projet.GetPtCaract()
        
        # Identification des items correspondants sur le doc SVG
        for p in doc.getElementsByTagName("path"):
            a = p.getAttribute("d")
            a = str(a).translate(None, 'MCLZ')  # Supprime les  lettres
            l = a.split()
            if len(l) > 1:      # On récupére le premier point du <path>
                x, y = l[0], l[1]
                x, y = float(x), float(y)
                
                for pt, obj, flag in pts_caract:
                    if match((x, y), pt) :
                        obj.cadre.append((p, flag))
                        if type(flag) != str:
                            break 
        
        # On lance la procédure d'enrichissement ...
        self.GetDocument().EnrichiSVGdoc(doc)
#        if self.typ == 'seq':
#            self.sequence.EnrichiSVG(doc)
#        elif self.typ == 'prj':
#            self.projet.EnrichiObjetsSVG(doc)
            
        doc.writexml(f, '   ', encoding = "utf-8")
        f.close

 
 
def Dialog_ErreurAccesFichier(nomFichier):
    messageErreur(None, u'Erreur !',
                  u"Impossible d'accéder en écriture au fichier\n\n%s" %toSystemEncoding(nomFichier))


########################################################################################
#
#
#  Classe définissant la fenétre "Séquence"
#
#
########################################################################################
class FenetreSequence(FenetreDocument):
    def __init__(self, parent, ouverture = False):
        self.typ = 'seq'
        FenetreDocument.__init__(self, parent)
        
        #
        # La classe
        #
        self.classe = Classe(parent, self.panelProp, ouverture = ouverture, typedoc = self.typ)
        
        #
        # La séquence
        #
        self.sequence = Sequence(self, self.classe, self.panelProp)
        self.classe.SetDocument(self.sequence)
      
        #
        # Arbre de structure de la séquence
        #
        arbre = ArbreSequence(self.pnl, self.sequence, self.classe,  self.panelProp)
        self.arbre = arbre
        self.arbre.SelectItem(self.classe.branche)
        self.arbre.ExpandAll()
        
        #
        # Permet d'ajouter automatiquement les systèmes des préférences
        #
        self.sequence.Initialise()
        
        #
        # Zone graphique de la fiche de séquence
        #
        self.fiche = FicheSequence(self.nb, self.sequence)
        self.nb.AddPage(self.fiche, u"Fiche Séquence")
        
        #
        # Détails
        #
        self.pageDetails = RapportRTF(self.nb, rt.RE_READONLY)
        self.nb.AddPage(self.pageDetails, u"Détails des séances")
        
        #
        # Bulletins Officiels
        #
        self.pageBO = Panel_BO(self.nb)
        self.nb.AddPage(self.pageBO, u"Bulletins Officiels")
        
        self.nb.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        
        self.miseEnPlace()
        
    
    ###############################################################################################
    def ajouterOutils(self):
        self.parent.supprimerOutils()
        
        self.parent.tb.InsertToolItem(5, self.parent.tool_ss)
        self.parent.tb.InsertToolItem(6, self.parent.tool_sy)

        self.parent.tb.Realize()
    
        
        
    ###############################################################################################
    def GetDocument(self):
        return self.sequence
        
        
    ###############################################################################################
    def OnPageChanged(self, event):
        new = event.GetSelection()
        event.Skip()
        if new == 1: # On vient de cliquer sur la page "détails"
            self.pageDetails.Remplir(self.fichierCourant, self.sequence, self.typ)
        
        elif new == 2: # On vient de cliquer sur la page "Bulletins Officiels"
            self.pageBO.Construire(REFERENTIELS[self.sequence.classe.typeEnseignement])
            
        elif new == 0: # On vient de cliquer sur la fiche
            self.fiche.Redessiner()
            
    ###############################################################################################
    def OnDocModified(self, event):
        if event.GetModif() != u"":
#            print "OnDocModified", event.GetModif()
            self.classe.undoStack.do(event.GetModif())
            self.sequence.undoStack.do(event.GetModif())
        
        if event.GetDocument() == self.sequence:
            self.sequence.VerifPb()
            if event.GetDraw():
                wx.CallAfter(self.fiche.Redessiner)
            self.MarquerFichierCourantModifie()
            
        elif event.GetDocument() == self.classe:
            self.sequence.VerifPb()
            if event.GetDraw():
                wx.CallAfter(self.fiche.Redessiner)
            self.MarquerFichierCourantModifie()
        
        self.parent.miseAJourUndo()
        
        
    ###############################################################################################
    def enregistrer(self, nomFichier):

        wx.BeginBusyCursor()
        fichier = file(nomFichier, 'w')
        
        # La séquence
        sequence = self.sequence.getBranche()
        classe = self.classe.getBranche()
        
        # La racine
        root = ET.Element("Sequence_Classe")
        root.append(sequence)
        root.append(classe)
        constantes.indent(root)
        
        ET.ElementTree(root).write(fichier, xml_declaration=False, encoding = SYSTEM_ENCODING)
        
        fichier.close()
        self.definirNomFichierCourant(nomFichier)
        self.MarquerFichierCourantModifie(False)
        wx.EndBusyCursor()
        
        
    ###############################################################################################
    def VerifierReparation(self):
        """ Vérification (et correction) de la compatibilité de la séquence avec la classe
            aprés une ouverture avec réparation
        """
#        print "VerifierReparation", self.sequence.CI.numCI, self.sequence.GetReferentiel().CentresInterets
        for ci in self.sequence.CI.numCI:
            if ci >= len(self.sequence.GetReferentiel().CentresInterets):
                self.sequence.CI.numCI.remove(ci)
                messageErreur(self,u"CI inexistant",
                              u"Pas de CI numéro " + str(ci) + " !\n\n" \
                              u"La séquence ouverte fait référence à un Centre d'Intérét\n" \
                              u"qui n'existe pas dans le référentiel par défaut.\n\n" \
                              u"Il a été supprimé !")
        return


    ###############################################################################################
    def restaurer(self):
        """ Restaure l'arbre de construction
            et redessine la fiche
            (après undo ou redo)
        """
        
        self.sequence.MiseAJourTypeEnseignement()
        t0 = time.time()
        
        #
        # Réinitialisation de l'arbre
        #
        self.arbre.DeleteAllItems()
        root = self.arbre.AddRoot("")
        t1 = time.time()
        print "  ", t1-t0
        
        self.classe.ConstruireArbre(self.arbre, root)
        t2 = time.time()
        print "  ", t2-t1
        
        self.sequence.ConstruireArbre(self.arbre, root)
        t3 = time.time()
        print "  ", t3-t2
        
        self.sequence.CI.SetNum()
        t4 = time.time()
        print "  ", t4-t3
        
        self.sequence.SetCodes()
        t5 = time.time()
        print "  ", t5-t4
        
        self.sequence.PubDescription()
        t6 = time.time()
        print "  ", t6-t5
        
        self.sequence.SetLiens()
        t7 = time.time()
        print "  ", t7-t6
        
        self.sequence.VerifPb()
        t8 = time.time()
        print "  ", t8-t7

        self.sequence.Verrouiller()
        t9 = time.time()
        print "  ", t9-t8
        
        self.arbre.SelectItem(self.classe.branche)
        t10 = time.time()
        print "  ", t10-t9
        
        self.arbre.Layout()
        self.arbre.ExpandAll()
        self.arbre.CalculatePositions()
        
        self.fiche.Redessiner()
        t11 = time.time()
        print "  ", t11-t10
        self.parent.miseAJourUndo()
        
        
        
    ###############################################################################################
    def ouvrir(self, nomFichier, redessiner = True, reparer = False):
#        print "ouvrir sequence"
        if not os.path.isfile(nomFichier):
            return
        
        fichier = open(nomFichier,'r')
        self.definirNomFichierCourant(nomFichier)
    
        def ouvre():
            root = ET.parse(fichier).getroot()
            
            # La séquence
            sequence = root.find("Sequence")
            if sequence == None: # Ancienne version , forcément STI2D-ETT !!
                if hasattr(self.classe, 'panelPropriete'):
                    self.classe.panelPropriete.EvtRadioBox(CodeFam = ('ET', 'STI'))
                self.sequence.setBranche(root)
            else:
                # La classe
                classe = root.find("Classe")
                self.classe.setBranche(classe, reparer = reparer)
                self.sequence.MiseAJourTypeEnseignement()
                self.sequence.setBranche(sequence)  

            if reparer:
                self.VerifierReparation()
                
            self.arbre.DeleteAllItems()
            root = self.arbre.AddRoot("")
            self.classe.ConstruireArbre(self.arbre, root)
            self.sequence.ConstruireArbre(self.arbre, root)
            self.sequence.CI.SetNum()
            self.sequence.SetCodes()
            self.sequence.PubDescription()
            self.sequence.SetLiens()
            self.sequence.VerifPb()
    
            self.sequence.Verrouiller()
            self.arbre.SelectItem(self.classe.branche)


        if "beta" in version.__version__:
            ouvre()
        else:
            try:
                ouvre()
            except:
                nomCourt = os.path.splitext(os.path.split(nomFichier)[1])[0]
                messageErreur(self,u"Erreur d'ouverture",
                              u"La séquence pédagogique\n    %s\n n'a pas pu étre ouverte !" %nomCourt)
                fichier.close()
                self.Close()
                return

        self.arbre.Layout()
        self.arbre.ExpandAll()
        self.arbre.CalculatePositions()
        
        fichier.close()
        
        if redessiner:
            wx.CallAfter(self.fiche.Redessiner)

        self.classe.undoStack.do(u"Ouverture de la Classe")
        self.sequence.undoStack.do(u"Ouverture de la Séquence")
        self.parent.miseAJourUndo()
        

    #############################################################################
    def definirNomFichierCourant(self, nomFichier = ''):
        self.fichierCourant = nomFichier
        self.sequence.SetPath(nomFichier)
        self.SetTitre()

    
    #############################################################################
    def AppliquerOptions(self):
        self.sequence.AppliquerOptions()   
    


########################################################################################
#
#
#  Classe définissant la fenétre "Séquence"
#
#
########################################################################################
class FenetreProjet(FenetreDocument):
    def __init__(self, parent):
        self.typ = 'prj'
        print "FenetreProjet"
        FenetreDocument.__init__(self, parent)
        
        self.Freeze()
        
        #
        # La classe
        #
        self.classe = Classe(parent, self.panelProp, pourProjet = True, typedoc = self.typ)
        
        #
        # Le projet
        #
        self.projet = Projet(self, self.classe, self.panelProp)
        self.classe.SetDocument(self.projet)
        
        #
        # Arbre de structure du projet
        #
        arbre = ArbreProjet(self.pnl, self.projet, self.classe,  self.panelProp)
        self.arbre = arbre
        self.arbre.SelectItem(self.classe.branche)
        self.arbre.ExpandAll()
        
        for t in self.projet.taches:
            t.SetCode()
        
        #
        # Zone graphique de la fiche de projet
        #
        self.fiche = FicheProjet(self.nb, self.projet)       
#        self.thread = ThreadRedess(self.fichePrj)
        self.nb.AddPage(self.fiche, u"Fiche Projet")
        
        #
        # Détails
        #
        self.pageDetails = RapportRTF(self.nb, rt.RE_READONLY)
        self.nb.AddPage(self.pageDetails, u"Tâches élèves détaillées")
        
        #
        # Dossier de validation
        #
        self.pageValid = genpdf.PdfPanel(self.nb)
        self.nb.AddPage(self.pageValid, u"Dossier de validation")
        
        #
        # Bulletins Officiels
        #
        self.pageBO = Panel_BO(self.nb)
        self.nb.AddPage(self.pageBO, u"Bulletins Officiels")
        
        self.miseEnPlace()
        
        wx.CallAfter(self.Thaw)
        self.nb.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        
        
    


    ###############################################################################################
    def ajouterOutils(self):
        self.parent.supprimerOutils()

        self.parent.tb.InsertToolItem(5,self.parent.tool_pe)
        self.parent.tb.InsertToolItem(6, self.parent.tool_pp)
        self.parent.tb.InsertToolItem(7, self.parent.tool_pt)
        self.parent.tb.InsertToolItem(7, self.parent.tool_pr)
        self.parent.tb.Realize()
        
    ###############################################################################################
    def GetDocument(self):
        return self.projet
    
    ###############################################################################################
    def AjouterTache(self, event = None):
        self.arbre.AjouterTache()
        
        
    ###############################################################################################
    def OnPageChanged(self, event):
        new = event.GetSelection()
        event.Skip()
        if new == 1: # On vient de cliquer sur la page "détails"
            self.pageDetails.Remplir(self.fichierCourant, self.projet, self.typ)
        
        elif new == 2: # On vient de cliquer sur la page "dossier de validation"
            self.pageValid.MiseAJour(self.projet, self)
            
        elif new == 3: # On vient de cliquer sur la page "Bulletins Officiels"
            self.pageBO.Construire(REFERENTIELS[self.projet.classe.typeEnseignement])

        elif new == 0: # On vient de cliquer sur la fiche
            self.fiche.Redessiner()
            
            
    ###############################################################################################
    def OnDocModified(self, event):
        if event.GetModif() != u"":
#            print "OnDocModified", event.GetModif()
            self.classe.undoStack.do(event.GetModif())
            self.projet.undoStack.do(event.GetModif())
            
        if event.GetDocument() == self.projet:
            self.projet.VerifPb()
            self.projet.SetCompetencesRevuesSoutenance(miseAJourPanel = False)
            if event.GetDraw():
                wx.CallAfter(self.fiche.Redessiner)

            self.MarquerFichierCourantModifie()
            
        self.parent.miseAJourUndo()
        
        
    ###############################################################################################
    def enregistrer(self, nomFichier):

        wx.BeginBusyCursor()
        fichier = file(nomFichier, 'w')
        
        # Le projet
        projet = self.projet.getBranche()
        classe = self.classe.getBranche()
        
        # La racine
        root = ET.Element("Projet_Classe")
        root.append(projet)
        root.append(classe)
        constantes.indent(root)
        
#        print ET.tostring(projet)#, encoding="utf8",  method="xml")
        try:
#            ET.ElementTree(root).write(fichier, encoding = SYSTEM_ENCODING)
            ET.ElementTree(root).write(fichier, xml_declaration=False, encoding = SYSTEM_ENCODING)
        except IOError:
            messageErreur(None, u"Accés refusé", 
                                  u"L'accés au fichier %s a été refusé !\n\n"\
                                  u"Essayer de faire \"Enregistrer sous...\"" %nomFichier)
        except UnicodeDecodeError:
            messageErreur(None, u"Erreur d'encodage", 
                                  u"Un caractére spécial empéche l'enregistrement du fichier !\n\n"\
                                  u"Essayer de le localiser et de le supprimer.\n"\
                                  u"Merci de reporter cette erreur au développeur.")
            
        fichier.close()
        self.definirNomFichierCourant(nomFichier)
        self.MarquerFichierCourantModifie(False)
        wx.EndBusyCursor()
        
        
    ###############################################################################################
    def restaurer(self):
        """ Restaure l'arbre de construction
            et redessine la fiche
            (après undo ou redo)
        """
        #
        # Réinitialisation de l'arbre
        #
        self.arbre.DeleteAllItems()
        root = self.arbre.AddRoot("")
        
        self.projet.SetCompetencesRevuesSoutenance()
   
        self.classe.ConstruireArbre(self.arbre, root)
        self.projet.ConstruireArbre(self.arbre, root)
        self.projet.OrdonnerTaches()
        self.projet.PubDescription()
        self.projet.MiseAJourDureeEleves()
        self.projet.MiseAJourNomProfs()

        self.projet.Verrouiller()
        
        self.arbre.Layout()
        self.arbre.ExpandAll()
        self.arbre.CalculatePositions()
        
        self.fiche.Redessiner()
        self.parent.miseAJourUndo()
        
        
        
    ###############################################################################################
    def ouvrir(self, nomFichier, redessiner = True, reparer = False):
        print "Ouverture projet", nomFichier
        tps1 = time.clock()
        Ok = True
        Annuler = False
        nbr_etapes = 11
        
        # Pour le suivi de l'ouverture
        nomCourt = os.path.splitext(os.path.split(nomFichier)[1])[0]
        
        message = nomCourt+"\n"
        dlg = myProgressDialog(u"Ouverture d'un projet",
                                   message,
                                   nbr_etapes,
                                   self.parent)
        
        self.fiche.Hide()
        
        fichier = open(nomFichier,'r')
        self.definirNomFichierCourant(nomFichier)
    
        
        def ouvre(fichier, message):
            root = ET.parse(fichier).getroot()
            count = 0
            Ok = True
            Annuler = False
                   
            # Le projet
            projet = root.find("Projet")
            if projet == None:
                self.projet.setBranche(root)
                
            else:
                # La classe
                message += u"Construction de la structure de la classe...\t"
                dlg.Update(count, message)
                count += 1
                classe = root.find("Classe")
                err = self.classe.setBranche(classe, reparer = reparer)
                if len(err) > 0 :
                    Ok = False
                    message += (u"\n  "+CHAR_POINT).join([e.getMessage() for e in err]) 
                message += u"\n"
                
#                print "V",self.classe.GetVersionNum()
                if self.classe.GetVersionNum() < 5:
                    messageErreur(None, u"Ancien programme", 
                                  u"Projet enregistré avec les indicateurs de compétence antérieurs à la session 2014\n\n"\
                                  u"Les indicateurs de compétence ne seront pas chargés.")
                
                # Le projet
                message += u"Construction de la structure du projet...\t"
                dlg.Update(count, message)
                count += 1
#                print "ref :", 
#                self.projet.classe = self.classe
                # Derniére vérification
                if self.projet.GetProjetRef() == None:
                    print "Pas bon référentiel"
                    self.classe.setBranche(classe, reparer = True)
                err = self.projet.setBranche(projet)
    
            
                if len(err) > 0 :
                    Ok = False
                    message += (u"\n  "+CHAR_POINT).join([e.getMessage() for e in err])
                message += u"\n"
                
            self.arbre.DeleteAllItems()
            root = self.arbre.AddRoot("")
            
            message += u"Traitement des revues...\t"
            dlg.Update(count, message)
            count += 1
            try:
                self.projet.SetCompetencesRevuesSoutenance()
                message += u"Ok\n"
            except:
                Ok = False
                Annuler = True
                message += u"Erreur !\n"
                print "Erreur 4"
                        
            return root, message, count, Ok, Annuler
        
        
        if "beta" in version.__version__:
#            print "beta"
            root, message, count, Ok, Annuler = ouvre(fichier, message)
            err = []
        else:
            try:
                err = []
                root, message, count, Ok, Annuler = ouvre(fichier, message)
            except:
                count = 0
                err = [constantes.Erreur(constantes.ERR_INCONNUE)]
                message += err[0].getMessage() + u"\n"
                Annuler = True
        
        #
        # Erreur fatale d'ouverture
        #
        if Annuler:
            message += u"\n\nLe projet n'a pas pu étre ouvert !\n\n"
            if len(err) > 0:
                message += u"\n   L'erreur concerne :"
                message += (u"\n"+CHAR_POINT).join([e.getMessage() for e in err])
            fichier.close()
            self.Close()
            count = nbr_etapes
            dlg.Update(count, message)
            dlg.Destroy()
#            wx.CallAfter(self.fiche.Show)
#            wx.CallAfter(self.fiche.Redessiner)
            return
        
        liste_actions = [[self.classe.ConstruireArbre, [self.arbre, root], {},
                         u"Construction de l'arborescence de la classe...\t"],
                         [self.projet.ConstruireArbre, [self.arbre, root], {},
                          u"Construction de l'arborescence du projet...\t"],
                         [self.projet.OrdonnerTaches, [], {},
                          u"Ordonnancement des tâches...\t"],
                         [self.projet.PubDescription, [], {},
                          u"Traitement des descriptions...\t"],
                         [self.projet.SetLiens, [], {},
                          u"Construction des liens...\t"],
                         [self.projet.MiseAJourDureeEleves, [], {},
                          u"Ajout des durées/évaluabilités dans l'arbre...\t"],
                         [self.projet.MiseAJourNomProfs, [], {},
                          u"Ajout des disciplines dans l'arbre...\t"],
                         ]
        
        for fct, arg, karg, msg in liste_actions:
            message += msg
            dlg.Update(count, message)
            count += 1
            try :
                fct(*arg, **karg)
                message += u"Ok\n"
            except:
                Ok = False
                message += constantes.Erreur(constantes.ERR_INCONNUE).getMessage() + u"\n"
            

        self.projet.Verrouiller()

        message += u"Tracé de la fiche...\t"
        dlg.Update(count, message)
        count += 1

#        self.arbre.SelectItem(self.classe.branche)

        self.arbre.Layout()
        self.arbre.ExpandAll()
        self.arbre.CalculatePositions()
        
        fichier.close()
    
        #
        # Vérification de la version des grilles
        #
        self.projet.VerifierVersionGrilles()
        
        tps2 = time.clock() 
        print "Ouverture :", tps2 - tps1

        if Ok:
            dlg.Destroy()
        else:
            dlg.Update(nbr_etapes, message)
            dlg.Raise()
            dlg.Close() 
    
        wx.CallAfter(self.fiche.Show)
        wx.CallAfter(self.fiche.Redessiner)
        
        self.classe.undoStack.do(u"Ouverture de la Classe")
        self.projet.undoStack.do(u"Ouverture du Projet")
        self.parent.miseAJourUndo()
#        wx.CallAfter(dlg.Raise)

    #############################################################################
    def genererGrilles(self, event = None):
        """ Génération de toutes les grilles d'évaluation
             - demande d'un dossier -
        """
        log = []
        
        dlg = wx.DirDialog(self, message = u"Emplacement des grilles", 
                            style=wx.DD_DEFAULT_STYLE|wx.CHANGE_DIR
                            )
#        dlg.SetFilterIndex(0)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            dlg.Destroy()
            dlgb = wx.ProgressDialog   (u"Génération des grilles",
                                        u"",
                                        maximum = len(self.projet.eleves),
                                        parent=self,
                                        style = 0
                                        | wx.PD_APP_MODAL
                                        | wx.PD_CAN_ABORT
                                        #| wx.PD_CAN_SKIP
                                        #| wx.PD_ELAPSED_TIME
    #                                    | wx.PD_ESTIMATED_TIME
    #                                    | wx.PD_REMAINING_TIME
                                        #| wx.PD_AUTO_HIDE
                                        )

            
            count = 0
            
            nomFichiers = {}
            for e in self.projet.eleves:
                nomFichiers[e.id] = e.GetNomGrilles(path = path)
#            print "nomFichiers", nomFichiers
            
            if not self.projet.TesterExistanceGrilles(nomFichiers):
                dlgb.Destroy()
                return
            
            
            for e in self.projet.eleves:
                log.extend(e.GenererGrille(nomFichiers = nomFichiers[e.id], messageFin = False))
                dlgb.Update(count, u"Traitement de la grille de \n\n"+e.GetNomPrenom())
                dlgb.Refresh()
                count += 1
                dlgb.Refresh()
           
            t = u"Génération des grilles terminée "
            if len(log) == 0:
                t += u"avec succès !\n\n"
            else:
                t += u"avec des erreurs :\n\n"
                t += u"\n".join(log)
            
            t += "\n\nDossier des grilles :\n" + path
            dlgb.Update(count, t)
            dlgb.Destroy() 
                
                
        else:
            dlg.Destroy()
        
        return list(set(log))
    
    
            
    #############################################################################
    def genererGrillesPdf(self, event = None):
        """ Génération de TOUTES les grilles d'évaluation au format pdf
             - demande d'un nom de fichier -
        """
        mesFormats = u"PDF (.pdf)|*.pdf"
        nomFichier = getNomFichier("Grilles", self.projet.intitule[:20], r".pdf")
        dlg = wx.FileDialog(self, u"Enregistrer les grilles d'évaluation",
                            defaultFile = nomFichier,
                            wildcard = mesFormats,
#                           defaultPath = globdef.DOSSIER_EXEMPLES,
                            style=wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR
                            #| wx.DD_DIR_MUST_EXIST
                            #| wx.DD_CHANGE_DIR
                            )

        if dlg.ShowModal() == wx.ID_OK:
            nomFichier = dlg.GetPath()
            dlg.Destroy()
            dlgb = myProgressDialog(u"Génération des grilles",
                                        u"",
                                        maximum = len(self.projet.eleves)+1,
                                        parent=self,
                                        style = 0
                                        | wx.PD_APP_MODAL
                                        | wx.PD_CAN_ABORT
                                        | wx.STAY_ON_TOP
                                        #| wx.PD_CAN_SKIP
                                        #| wx.PD_ELAPSED_TIME
    #                                    | wx.PD_ESTIMATED_TIME
    #                                    | wx.PD_REMAINING_TIME
                                        #| wx.PD_AUTO_HIDE
                                        )
            
            
            count = 0
            
            pathprj = self.projet.GetPath()
#            print "pathprj", pathprj
            
            #
            # Détermination des fichiers grille à créer
            #
            nomFichiers = {}
            for e in self.projet.eleves:
                if len(e.grille) == 0: # Pas de fichier grille connu pour cet élève
                    nomFichiers[e.id] = e.GetNomGrilles(path = os.path.split(nomFichier)[0])
                else:
                    for g in e.grille.values():
                        if not os.path.exists(g.path): # Le fichier grille pour cet élève n'a pas été trouvé
                            nomFichiers[e.id] = e.GetNomGrilles(path = os.path.split(nomFichier)[0])
#            print "nomFichiers grille", nomFichiers
            
            # Si des fichiers existent avec le méme nom, on demande si on peut les écraser
            if not self.projet.TesterExistanceGrilles(nomFichiers):
                dlgb.Destroy()
                return
            
            try:
                dlgb.top()
            except:
                print "Top erreur"
            
#            dicInfo = self.projet.GetProjetRef().cellulesInfo
#            classNON = dicInfo["NON"][0][0]
#            feuilNON = dicInfo["NON"][0][1]
#            collectif = self.projet.GetProjetRef().grilles[classNON][1] == 'C'
            
            # Elaboration de la liste des fichiers/feuilles à exporter en PDF
            lst_grilles = []
            for e in self.projet.eleves:
                dlgb.Update(count, u"Traitement de la grille de \n\n"+e.GetNomPrenom())
                dlgb.Refresh()
                    
                if e.id in nomFichiers.keys():
                    e.GenererGrille(nomFichiers = nomFichiers[e.id], messageFin = False)

                for k, g in e.grille.items():
#                    grille = os.path.join(toFileEncoding(pathprj), toFileEncoding(g.path))
                    grille = os.path.join(pathprj, g.path)
                    if k in self.projet.GetReferentiel().aColNon.keys():
#                    if k == classNON:
                        collectif = self.projet.GetProjetRef().grilles[k][1] == 'C'
                        feuilNON = self.projet.GetProjetRef().cellulesInfo[k]["NON"][0][0]
                        if feuilNON != '' and collectif: # fichier "Collectif"
                            feuille = feuilNON+str(e.id+1)
                        else:
                            feuille = None
                    else:
                        feuille = None
                
                    lst_grilles.append((grille, feuille))
                
                count += 1
                dlgb.Refresh()
            
            dlgb.Update(count, u"Compilation des grilles ...\n\n")
            count += 1
            dlgb.Refresh()
                
            genpdf.genererGrillePDF(nomFichier, lst_grilles)
            
            dlgb.Update(count, u"Les grilles ont été créées avec succés dans le fichier :\n\n"+nomFichier)
            try:
                os.startfile(nomFichier)
            except:
                pass
            
            dlgb.Destroy()
                
                
        else:
            dlg.Destroy()
            
            
            
    #############################################################################
    def genererFicheValidation(self, event = None):
#        mesFormats = "Tableur Excel (.xls)|*.xls"
        
#        def getNomFichier(prefixe, projet):
#            nomFichier = prefixe+"_"+projet.intitule[:20]
#            for c in ["\"", "/", "\", ", "?", "<", ">", "|", ":", "."]:
#                nomFichier = nomFichier.replace(c, "_")
#            return nomFichier+".pdf"
        
        mesFormats = u"PDF (.pdf)|*.pdf"
        nomFichier = getNomFichier("FicheValidation", self.projet.intitule[:20], r".pdf")
        dlg = wx.FileDialog(self, u"Enregistrer le dossier de validation",
                            defaultFile = nomFichier,
                            wildcard = mesFormats,
#                           defaultPath = globdef.DOSSIER_EXEMPLES,
                            style=wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR
                            #| wx.DD_DIR_MUST_EXIST
                            #| wx.DD_CHANGE_DIR
                            )
        
        
        
#        dlg = wx.DirDialog(self, message = u"Emplacement de la fiche", 
#                            style=wx.DD_DEFAULT_STYLE|wx.CHANGE_DIR
#                            )
#        dlg.SetFilterIndex(0)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            dlg.Destroy()
            nomFichier = path
#            nomFichier = getNomFichier("FicheValidation", self.projet)
#            nomFichier = os.path.join(path, nomFichier)

            try:
                genpdf.genererDossierValidation(nomFichier, self.projet, self)
                os.startfile(nomFichier)
            except IOError:
                messageErreur(self, u"Erreur !",
                                  u"Impossible d'enregistrer le fichier.\n\nVérifier :\n" \
                                  u" - qu'aucun fichier portant le méme nom n'est déja ouvert\n" \
                                  u" - que le dossier choisi n'est pas protégé en écriture\n\n" \
                                  + nomFichier)
                wx.EndBusyCursor()
            
#            for t, f in tf:
#                try:
#                    t.save(os.path.join(path, f))
#                except:
#                    messageErreur(self, u"Erreur !",
#                                  u"Impossible d'enregistrer le fichier.\n\nVérifier :\n" \
#                                  u" - qu'aucun fichier portant le méme nom n'est déja ouvert\n" \
#                                  u" - que le dossier choisi n'est pas protégé en écriture")
#                t.close()
#            
#            dlgb.Update(count, u"Toutes les grilles ont été créées avec succés dans le dossier :\n\n"+path)
#            dlgb.Destroy() 
#                
                
        else:
            dlg.Destroy()
            
            
    #############################################################################
    def definirNomFichierCourant(self, nomFichier = ''):
        self.fichierCourant = nomFichier
#        self.projet.SetPath(nomFichier)
        self.SetTitre()

    
    #############################################################################
    def AppliquerOptions(self):
        self.projet.AppliquerOptions() 
    
    
#class ThreadRedess(Thread):
#    def __init__(self, fiche):
#        Thread.__init__(self)
#        self.fiche = fiche
#        
#    def run(self):
#        self.fiche.enCours = True
#        self.fiche.Redessiner()
#        Thread.__init__(self)
#        self.fiche.enCours = False

        
####################################################################################
#
#   Classe définissant la base de la fenétre de fiche
#
####################################################################################
class BaseFiche(wx.ScrolledWindow):
    def __init__(self, parent):
#        wx.Panel.__init__(self, parent, -1)
        wx.ScrolledWindow.__init__(self, parent, -1, style = wx.VSCROLL | wx.RETAINED)
        
        self.EnableScrolling(False, True)
        self.SetScrollbars(20, 20, 50, 50);
        
        self.enCours = False
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_LEFT_UP, self.OnClick)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDClick)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRClick)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)
        self.Bind(wx.EVT_MOTION, self.OnMove)
#        self.Bind(wx.EVT_SCROLLWIN, self.OnScroll)
        
        self.InitBuffer()

    ######################################################################################################
    def OnLeave(self, evt = None):
        if hasattr(self, 'call') and self.call.IsRunning():
            self.call.Stop()
#        if hasattr(self, 'tip') 
#            self.tip.Show(False)

    ######################################################################################################
    def OnEnter(self, event):
#        print "OnEnter Fiche"
        self.SetFocus()
        event.Skip()
        
        
    #############################################################################            
    def OnResize(self, evt):
        w = self.GetClientSize()[0]
        self.SetVirtualSize((w,w*29/21)) # Mise au format A4

        self.InitBuffer()
        if w > 0 and self.IsShown():
            self.Redessiner()


    #############################################################################            
    def OnScroll(self, evt):
        self.Refresh()



    #############################################################################            
    def OnPaint(self, evt):
#        print "OnPaint"
#        dc = wx.BufferedPaintDC(self, self.buffer, wx.BUFFER_VIRTUAL_AREA)
        dc = wx.PaintDC(self)
        self.PrepareDC(dc)
        dc.DrawBitmap(self.buffer, 0,0) 
        
        
    #############################################################################            
    def CentrerSur(self, obj):
        if hasattr(obj, 'rect'):
            y = (obj.rect[0][1])*self.GetVirtualSizeTuple()[1]
            self.Scroll(0, y/20)
            self.Refresh()
    
    
    #############################################################################            
    def OnClick(self, evt):
        _x, _y = self.CalcUnscrolledPosition(evt.GetX(), evt.GetY())
        xx, yy = self.ctx.device_to_user(_x, _y)
        
        #
        # Changement de branche sur l'arbre
        #
        branche = self.GetDoc().HitTest(xx, yy)
        if branche != None:
            self.GetDoc().SelectItem(branche, depuisFiche = True)
            
            
        if self.GetDoc().pasVerouille:
            #
            # Autres actions
            #
            position = self.GetDoc().HitTestPosition(xx, yy)
            if position != None:
                if hasattr(self, 'projet'):
                    self.projet.SetPosition(position)
                else:
                    self.sequence.SetPosition(position)
                    if hasattr(self.GetDoc(), 'panelPropriete'):
                        self.GetDoc().panelPropriete.SetBitmapPosition(bougerSlider = position)
            
        return branche
    
    
    #############################################################################            
    def OnDClick(self, evt):
        item = self.OnClick(evt)
        if item != None:
            self.GetDoc().AfficherLien(item)
            
            
    #############################################################################            
    def OnRClick(self, evt):
        item = self.OnClick(evt)
        if item != None:
            self.GetDoc().AfficherMenuContextuel(item)
            
            
    #############################################################################            
    def InitBuffer(self):
        w,h = self.GetVirtualSize()
        self.buffer = wx.EmptyBitmap(w,h)


    #############################################################################            
    def Redessiner(self, event = None):  
        
        def redess():
            wx.BeginBusyCursor()
                
    #        tps1 = time.clock() 
                
            
    #        face = wx.lib.wxcairo.FontFaceFromFont(wx.FFont(10, wx.SWISS, wx.FONTFLAG_BOLD))
    #        ctx.set_font_face(face)
            
            cdc = wx.ClientDC(self)
            self.PrepareDC(cdc) 
            dc = wx.BufferedDC(cdc, self.buffer, wx.BUFFER_VIRTUAL_AREA)
            dc.SetBackground(wx.Brush('white'))
            dc.Clear()
            ctx = wx.lib.wxcairo.ContextFromDC(dc)
            dc.BeginDrawing()
            self.normalize(ctx)
            
            self.Draw(ctx)
            
    #        b = Thread(None, self.Draw, None, (ctx,))
    #        b.start()
            
            dc.EndDrawing()
            self.ctx = ctx
            self.Refresh()
    
    #        tps2 = time.clock() 
    #        print "Tracé :"#, tps2 - tps1
            
            wx.EndBusyCursor()
            
        redess()


    
    #############################################################################            
    def normalize(self, cr):
        h = float(self.GetVirtualSize()[1])
        if h <= 0:
            h = float(100)
        cr.scale(h, h) 
        
        
        
        
        
        
        
        
####################################################################################
#
#   Classe définissant la fenétre de la fiche de séquence
#
####################################################################################
class FicheSequence(BaseFiche):
    def __init__(self, parent, sequence):
        BaseFiche.__init__(self, parent)
        self.sequence = sequence


    ######################################################################################################
    def GetDoc(self):
        return self.sequence
       
    ######################################################################################################
    def OnMove(self, evt):
        if hasattr(self, 'tip'):
            self.tip.Show(False)
            self.call.Stop()
        x, y = evt.GetPosition()
        _x, _y = self.CalcUnscrolledPosition(x, y)
        xx, yy = self.ctx.device_to_user(_x, _y)
        branche = self.sequence.HitTest(xx, yy)
        if branche != None:
            elem = branche.GetData()
            if hasattr(elem, 'tip'):
                x, y = self.ClientToScreen((x, y))
                elem.tip.Position((x,y), (0,0))
                self.call = wx.CallLater(500, elem.tip.Show, True)
                self.tip = elem.tip
        evt.Skip()


    #############################################################################            
    def Draw(self, ctx):
        draw_cairo_seq.Draw(ctx, self.sequence)
        
        
#    #############################################################################            
#    def OnClick(self, evt):
#        x, y = evt.GetX(), evt.GetY()
#        _x, _y = self.CalcUnscrolledPosition(x, y)
#        xx, yy = self.ctx.device_to_user(_x, _y)
#        
#        #
#        # Changement de branche sur l'arbre
#        #
#        branche = self.sequence.HitTest(xx, yy)
#        if branche != None:
#            self.sequence.arbre.SelectItem(branche)
#
#
#        #
#        # Autres actions
#        #
#        position = self.sequence.HitTestPosition(xx, yy)
#        if position != None:
#            self.sequence.SetPosition(position)
#            if hasattr(self.sequence, 'panelPropriete'):
#                self.sequence.panelPropriete.SetBitmapPosition(bougerSlider = position)
#            
#        return branche
    
    



    
####################################################################################
#
#   Classe définissant la fenétre de la fiche de séquence
#
####################################################################################
class FicheProjet(BaseFiche):
    def __init__(self, parent, projet):
        BaseFiche.__init__(self, parent)
        self.projet = projet
        
        #
        # Création du Tip (PopupInfo) pour les compétences
        #
        l = 0
        popup = PopupInfo2(self.projet.GetApp(), u"Compétence")
        popup.sizer.SetItemSpan(popup.titre, (1,2)) 
        l += 1
        
        self.tip_comp = popup.CreerTexte((l,0), (1,2), flag = wx.ALL)
        self.tip_comp.SetForegroundColour("CHARTREUSE4")
        self.tip_comp.SetFont(wx.Font(11, wx.SWISS, wx.FONTSTYLE_NORMAL, wx.NORMAL))
        l += 1
        
        self.tip_arbre = popup.CreerArbre((l,0), (1,2), projet.GetReferentiel(), flag = wx.ALL)
        l += 1
        
        self.lab_legend = {}
        for i, (part , tit) in enumerate(self.projet.GetProjetRef().parties.items()):
            self.lab_legend[part] = popup.CreerTexte((l,i), txt = tit, flag = wx.ALIGN_RIGHT|wx.RIGHT)
            self.lab_legend[part].SetFont(wx.Font(8, wx.SWISS, wx.FONTSTYLE_ITALIC, wx.NORMAL))
            self.lab_legend[part].SetForegroundColour(constantes.COUL_PARTIE[part])
            
            
#        self.lab_legend1 = popup.CreerTexte((l,0), txt = u"Conduite", flag = wx.ALIGN_RIGHT|wx.RIGHT)
#        self.lab_legend1.SetFont(wx.Font(8, wx.SWISS, wx.FONTSTYLE_ITALIC, wx.NORMAL))
#        self.lab_legend1.SetForegroundColour(constantes.COUL_PARTIE['C'])
#        
#        self.lab_legend2 = popup.CreerTexte((l,1), txt = u"Soutenance", flag = wx.ALIGN_LEFT|wx.LEFT)
#        self.lab_legend2.SetFont(wx.Font(8, wx.SWISS, wx.FONTSTYLE_ITALIC, wx.NORMAL))
#        self.lab_legend2.SetForegroundColour(constantes.COUL_PARTIE['S'])
        
        self.popup = popup
#        self.MiseAJourTypeEnseignement(self.projet.classe.typeEnseignement)
        
    ######################################################################################################
    def GetDoc(self):
        return self.projet
            
    ######################################################################################################
    def OnMove(self, evt):
        
        if hasattr(self, 'tip'):
            self.tip.Show(False)
            self.call.Stop()
        
        x, y = evt.GetPosition()
        _x, _y = self.CalcUnscrolledPosition(x, y)
        xx, yy = self.ctx.device_to_user(_x, _y)
        evt.Skip()
        
        #
        # Cas général
        #
        branche = self.projet.HitTest(xx, yy)
        if branche != None:
            elem = branche.GetData()
            if hasattr(elem, 'tip'):
                x, y = self.ClientToScreen((x, y))
                elem.tip.Position((x,y), (0,0))
                self.call = wx.CallLater(500, elem.tip.Show, True)
                self.tip = elem.tip
                evt.Skip()
                return    
        
        #
        # Cas particulier des compétences
        #
        kCompObj = self.projet.HitTestCompetence(xx, yy)
        if kCompObj != None:
            kComp, obj = kCompObj
            if hasattr(self, 'popup'):
#                for tip in self.tip_indic:
#                    tip.Destroy()
#                self.tip_indic = []
                x, y = self.ClientToScreen((x, y))
#                type_ens = self.projet.classe.typeEnseignement
                prj = self.projet.GetProjetRef()
                competence = prj.getCompetence(kComp)
                        
                intituleComp = competence[0]
                
                k = kComp.split(u"\n")
                if len(k) > 1:
                    titre = u"Compétences\n"+u"\n".join(k)
                else:
                    titre = u"Compétence\n"+k[0]
                self.popup.SetTitre(titre)
             
                intituleComp = "\n".join([textwrap.fill(ind, 50) for ind in intituleComp.split(u"\n")]) 
             
                self.popup.SetTexte(intituleComp, self.tip_comp)
                
                self.tip_arbre.DeleteChildren(self.tip_arbre.root)
                if type(competence[1]) == dict:  
                    indicEleve = obj.GetDicIndicateurs()
                else:
                    indicEleve = obj.GetDicIndicateurs()[kComp]
                self.tip_arbre.Construire(competence[1], indicEleve, prj)
                
                self.popup.Fit()

                self.popup.Position((x,y), (0,0))
                self.call = wx.CallLater(500, self.popup.Show, True)
                self.tip = self.popup
            
        evt.Skip()


    #############################################################################
#    def MiseAJourTypeEnseignement(self, type_ens):
#        print u"Sert à rien", a
#        texte = u"Indicateur"
#        ref = self.projet.GetReferentiel()
#        if ref.prof_Comp <= 1:
#            texte += u"s"
#        self.popup.SetTexte(texte, self.lab_indic)
#        self.tip_compp.Show(ref.prof_Comp > 1)
#        self.tip_poids.Show(type_ens == "SSI")
            
        
    #############################################################################            
    def Draw(self, ctx):
        draw_cairo_prj.Draw(ctx, self.projet)
        
        
    
    
####################################################################################
#
#   Classe définissant le panel conteneur des panels de propriétés
#
####################################################################################    
class PanelConteneur(wx.Panel):    
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)#, style = wx.BORDER_SIMPLE)
        
        self.bsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.bsizer)
        
        #
        # Le panel affiché
        #
        self.panel = None
    
    
    def AfficherPanel(self, panel):
#        print "afficher", panel
        if self.panel != None:
            self.bsizer.Detach(self.panel)
            self.panel.Hide()
        
        self.panel = panel
        self.bsizer.Add(self.panel, 1, flag = wx.EXPAND|wx.GROW)
        self.panel.Show()
        self.bsizer.Layout()
#        self.panel.Refresh()
#        self.Refresh()        
    

                         
                
####################################################################################
#
#   Classe définissant le panel de propriété par défaut
#
####################################################################################
DELAY = 100 # Delai en millisecondes avant de rafraichir l'affichage suite à un saisie au clavier
class PanelPropriete(scrolled.ScrolledPanel):
    def __init__(self, parent, titre = u"", objet = None, style = wx.VSCROLL | wx.RETAINED):
        scrolled.ScrolledPanel.__init__(self, parent, -1, style = style)#|wx.BORDER_SIMPLE)
        
        self.sizer = wx.GridBagSizer()
        self.Hide()
#        self.SetMinSize((400, 200))
        self.SetSizer(self.sizer)
        self.SetAutoLayout(True)
#        self.SetScrollRate(20,20)
#        self.SetupScrolling() # Cause des problémes 
#        self.EnableScrolling(True, True)
        self.eventAttente = False
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)


    ######################################################################################################
    def OnEnter(self, event):
#        print "OnEnter PanelPropriete"
        self.SetFocus()
        event.Skip()

       
    #########################################################################################################
    def sendEvent(self, doc = None, modif = u"", draw = True, obj = None):
        self.eventAttente = False
        evt = SeqEvent(myEVT_DOC_MODIFIED, self.GetId())
        if doc != None:
            evt.SetDocument(doc)
        else:
            evt.SetDocument(self.GetDocument())
        
        if modif != u"":
            evt.SetModif(modif)
            
        evt.SetDraw(draw)
        
        self.GetEventHandler().ProcessEvent(evt)
        
    def GetFenetreDoc(self):
        return self.GetDocument().app
        
####################################################################################
#
#   Classe définissant le panel "racine" (ne contenant que des infos HTML)
#
####################################################################################
import wx.richtext as rt
class PanelPropriete_Racine(wx.Panel):
    def __init__(self, parent, texte):
        wx.Panel.__init__(self, parent, -1)
        self.Hide()
        
        self.rtc = rt.RichTextCtrl(self, style=rt.RE_READONLY|wx.NO_BORDER)#
        wx.CallAfter(self.rtc.SetFocus)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.rtc, 1,flag = wx.EXPAND)
        self.SetSizer(sizer)

        out = cStringIO.StringIO()
        handler = rt.RichTextXMLHandler()
        buff = self.rtc.GetBuffer()
#        buff.AddHandler(handler)
        out.write(texte)
        out.seek(0)
        handler.LoadStream(buff, out)
        self.rtc.Refresh()
        
        sizer.Layout()
#        wx.CallAfter(self.Layout)
        self.Layout()

#    def GetNiveau(self):
#        return 0
     

####################################################################################
#
#   Classe définissant le panel de propriété de séquence
#
####################################################################################
class PanelPropriete_Sequence(PanelPropriete):
    def __init__(self, parent, sequence):
        PanelPropriete.__init__(self, parent)
        self.sequence = sequence
        
        titre = wx.StaticBox(self, -1, u"Intitulé de la séquence")
        sb = wx.StaticBoxSizer(titre)
        textctrl = wx.TextCtrl(self, -1, u"", style=wx.TE_MULTILINE)
        sb.Add(textctrl, 1, flag = wx.EXPAND)
        self.textctrl = textctrl
        self.sizer.Add(sb, (0,0), flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT|wx.LEFT|wx.EXPAND, border = 2)
#        self.sizer.Add(textctrl, (0,1), flag = wx.EXPAND)
        self.Bind(wx.EVT_TEXT, self.EvtText, textctrl)
        
        titre = wx.StaticBox(self, -1, u"Commentaires")
        sb = wx.StaticBoxSizer(titre)
        commctrl = wx.TextCtrl(self, -1, u"", style=wx.TE_MULTILINE)
        sb.Add(commctrl, 1, flag = wx.EXPAND)
        self.commctrl = commctrl
        self.sizer.Add(sb, (0,1), (2,1),  flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT|wx.LEFT|wx.EXPAND, border = 2)
#        self.sizer.Add(commctrl, (1,1), flag = wx.EXPAND)
        self.Bind(wx.EVT_TEXT, self.EvtText, commctrl)
        self.sizer.AddGrowableCol(1)
        
        titre = wx.StaticBox(self, -1, u"Position")
        sb = wx.StaticBoxSizer(titre, wx.VERTICAL)
        self.bmp = wx.StaticBitmap(self, -1, self.getBitmapPeriode(250))
        position = wx.Slider(self, -1, self.sequence.position, 0, self.sequence.GetReferentiel().getNbrPeriodes()-1, (30, 60), (250, -1), 
            wx.SL_HORIZONTAL | wx.SL_AUTOTICKS |wx.SL_TOP 
            )
        sb.Add(self.bmp)
        sb.Add(position)
        self.position = position
        self.sizer.Add(sb, (1,0), flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT|wx.LEFT, border = 2)
        position.Bind(wx.EVT_SCROLL_CHANGED, self.onChanged)
        
        self.sizer.Layout()
#        wx.CallAfter(self.Layout)
        self.Layout()
        
#        self.Fit()
        
    
    #############################################################################            
    def getBitmapPeriode(self, larg):
        w, h = 0.04*5, 0.04
        imagesurface = cairo.ImageSurface(cairo.FORMAT_ARGB32,  larg, int(h/w*larg))#cairo.FORMAT_ARGB32,cairo.FORMAT_RGB24
        ctx = cairo.Context(imagesurface)
        ctx.scale(larg/w, larg/w) 
        draw_cairo_seq.DrawPeriodes(ctx, (0,0,w,h), self.sequence.position,
                                    self.sequence.GetReferentiel().periodes)

        bmp = wx.lib.wxcairo.BitmapFromImageSurface(imagesurface)
        
        # On fait une copie sinon éa s'efface ...
        img = bmp.ConvertToImage()
        bmp = img.ConvertToBitmap()
        
        return bmp
         
    
    #############################################################################            
    def onChanged(self, evt):
        self.sequence.SetPosition(evt.EventObject.GetValue())
        self.SetBitmapPosition()
        
        
    #############################################################################            
    def SetBitmapPosition(self, bougerSlider = None):
        self.sendEvent(modif = u"Changement de position de la séquence",
                       obj = self.sequence)
        self.bmp.SetBitmap(self.getBitmapPeriode(250))
        if bougerSlider != None:
            self.position.SetValue(bougerSlider)
        
    #############################################################################            
    def EvtText(self, event):
        if event.GetEventObject() == self.textctrl:
            self.sequence.SetText(event.GetString())
            t = u"Modification de l'intitulé de la séquence"
        else:
            self.sequence.SetCommentaire(event.GetString())
            t = u"Modification du commentaire de la séquence"
        if not self.eventAttente:
            wx.CallLater(DELAY, self.sendEvent, modif = t)
            self.eventAttente = True
        
    #############################################################################            
    def MiseAJour(self, sendEvt = False):
#        print "Miseàjour"
        self.textctrl.ChangeValue(self.sequence.intitule)
        
        self.position.SetMax(self.sequence.GetReferentiel().getNbrPeriodes()-1)
        self.sequence.position = min(self.sequence.position, self.sequence.GetReferentiel().getNbrPeriodes()-1)
        self.position.SetValue(self.sequence.position)
        self.bmp.SetBitmap(self.getBitmapPeriode(250))
        self.Layout()
        if sendEvt:
            self.sendEvent()

    #############################################################################            
    def GetDocument(self):
        return self.sequence
    
    
####################################################################################
#
#   Classe définissant le panel de propriété du projet
#
####################################################################################
class PanelPropriete_Projet(PanelPropriete):
    def __init__(self, parent, projet):
        PanelPropriete.__init__(self, parent)
        
        self.projet = projet
        
        self.nb = wx.Notebook(self, -1,  size = (21,21), style= wx.BK_DEFAULT)
        
        self.construire()
        
        self.sizer.Add(self.nb, (0,0), flag = wx.EXPAND)
        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableRow(0)
#        self.sizer.Layout()
        
        self.Layout()
        self.FitInside()
        wx.CallAfter(self.PostSizeEvent)
        
        self.MiseAJourTypeEnseignement()
        
        self.Show()
        
#        self.Fit()
        
    #############################################################################            
    def GetPageNum(self, win):
        for np in range(self.nb.GetPageCount()):
            if self.nb.GetPage(np) == win:
                return np
        
    #############################################################################            
    def creerPageSimple(self, fct):
        bg_color = self.Parent.GetBackgroundColour()
        page = PanelPropriete(self.nb)
        page.SetBackgroundColour(bg_color)
        self.nb.AddPage(page, u"")
        ctrl = wx.TextCtrl(page, -1, u"", style=wx.TE_MULTILINE)
        page.Bind(wx.EVT_TEXT, fct, ctrl)
        page.sizer.Add(ctrl, (0,0), flag = wx.EXPAND)
        page.sizer.AddGrowableCol(0)
        page.sizer.AddGrowableRow(0)  
        page.sizer.Layout()
        return page, ctrl, self.nb.GetPageCount()-1
    
    
    #############################################################################            
    def construire(self):
#        ref = self.projet.GetReferentiel()
        self.pages = {}
        
        
        #
        # La page "Généralités"
        #
        pageGen = PanelPropriete(self.nb)
        bg_color = self.Parent.GetBackgroundColour()
        pageGen.SetBackgroundColour(bg_color)
        self.pageGen = pageGen
        self.nb.AddPage(pageGen, u"Propriétés générales")
        
            
        #
        # Intitulé du projet (TIT)
        #
        self.titre = wx.StaticBox(pageGen, -1, u"")
        sb = wx.StaticBoxSizer(self.titre)
        textctrl = wx.TextCtrl(pageGen, -1, u"", style=wx.TE_MULTILINE)
        sb.Add(textctrl, 1, flag = wx.EXPAND)
        self.textctrl = textctrl
        pageGen.sizer.Add(sb, (0,0), flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT|wx.LEFT|wx.EXPAND, border = 2)
        pageGen.Bind(wx.EVT_TEXT, self.EvtText, textctrl)
        
        
        #
        # Problématique (PB)
        #
        self.tit_pb = wx.StaticBox(pageGen, -1, u"")
        sb = wx.StaticBoxSizer(self.tit_pb)
        self.commctrl = wx.TextCtrl(pageGen, -1, u"", style=wx.TE_MULTILINE)
        sb.Add(self.commctrl, 1, flag = wx.EXPAND)
        pageGen.sizer.Add(sb, (0,1), (2,1),  flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT|wx.LEFT|wx.EXPAND, border = 2)
        pageGen.Bind(wx.EVT_TEXT, self.EvtText, self.commctrl)
        pageGen.sizer.AddGrowableCol(1)
        
        
        #
        # Année scolaire et Position dans l'année
        #
        titre = wx.StaticBox(pageGen, -1, u"Année et Position")
        sb = wx.StaticBoxSizer(titre, wx.VERTICAL)
        
        self.annee = Variable(u"Année scolaire", lstVal = self.projet.annee, 
                                   typ = VAR_ENTIER_POS, bornes = [2012,2100])
        self.ctrlAnnee = VariableCtrl(pageGen, self.annee, coef = 1, signeEgal = False,
                                      help = u"Année scolaire", sizeh = 40, 
                                      unite = str(self.projet.annee+1),
                                      sliderAGauche = True)
        self.Bind(EVT_VAR_CTRL, self.EvtVariable, self.ctrlAnnee)
        sb.Add(self.ctrlAnnee)
        
        self.bmp = wx.StaticBitmap(pageGen, -1, self.getBitmapPeriode(250))
        position = wx.Slider(pageGen, -1, self.projet.position, 0, 5, (30, 60), (190, -1), 
            wx.SL_HORIZONTAL | wx.SL_TOP)#wx.SL_AUTOTICKS |
        sb.Add(self.bmp)
        sb.Add(position)
        self.position = position
        pageGen.sizer.Add(sb, (1,0), flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT|wx.EXPAND|wx.LEFT, border = 2)
        position.Bind(wx.EVT_SCROLL_CHANGED, self.onChanged)
        
        #
        # Organisation (nombre et positions des revues)
        #
        self.panelOrga = PanelOrganisation(pageGen, self, self.projet)
        pageGen.sizer.Add(self.panelOrga, (0,2), (2,1), flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT|wx.EXPAND|wx.LEFT, border = 2)
        pageGen.sizer.AddGrowableRow(0)

        
        
        #
        # La page "Enoncé général du besoin" ('ORI')
        #
#        self.pages['ORI'] = self.creerPageSimple(self.EvtText)
#        self.pageBG = PanelPropriete(self.nb)
#        self.pageBG.SetBackgroundColour(bg_color)
#        self.nb.AddPage(self.pageBG, u"")
#        self.bgctrl = wx.TextCtrl(self.pageBG, -1, u"", style=wx.TE_MULTILINE)
#        self.pageBG.Bind(wx.EVT_TEXT, self.EvtText, self.bgctrl)
#        self.pageBG.sizer.Add(self.bgctrl, (0,0), flag = wx.EXPAND)
#        self.pageBG.sizer.AddGrowableCol(0)
#        self.pageBG.sizer.AddGrowableRow(0)  
#        self.pageBG.sizer.Layout()
        
        
        #
        # La page "Contraintes Imposées" (CCF)
        #
#        self.pages['CCF'] = self.creerPageSimple(self.EvtText)
#        self.pageCont = PanelPropriete(self.nb)
#        self.pageCont.SetBackgroundColour(bg_color)
#        self.nb.AddPage(self.pageCont, u"")  
#        self.contctrl = wx.TextCtrl(self.pageCont, -1, u"", style=wx.TE_MULTILINE)
#        self.pageCont.Bind(wx.EVT_TEXT, self.EvtText, self.contctrl)
#        self.pageCont.sizer.Add(self.contctrl, (0,0), flag = wx.EXPAND)
#        self.pageCont.sizer.AddGrowableCol(0)
#        self.pageCont.sizer.AddGrowableRow(0)  
#        self.pageCont.sizer.Layout()
        
        
        
        
        
        #
        # La page "Production attendue" ('OBJ')
        #
#        self.pages['OBJ'] = self.creerPageSimple(self.EvtText)
#        self.pageProd = PanelPropriete(self.nb)
#        self.pageProd.SetBackgroundColour(bg_color)
#        self.nb.AddPage(self.pageProd, u"")
#        self.prodctrl = wx.TextCtrl(self.pageProd, -1, u"", style=wx.TE_MULTILINE)
#        self.pageProd.Bind(wx.EVT_TEXT, self.EvtText, self.prodctrl)
#        self.pageProd.sizer.Add(self.prodctrl, (0,0), flag = wx.EXPAND)
#        self.pageProd.sizer.AddGrowableCol(0)
#        self.pageProd.sizer.AddGrowableRow(0)  
#        self.pageProd.sizer.Layout()
    
    
    #############################################################################            
    def getBitmapPeriode(self, larg):
#        print "getBitmapPeriode"
#        print "  ", self.projet.position
#        print "  ", self.projet.GetReferentiel().periodes
#        print "  ", self.projet.GetReferentiel().periode_prj
        w, h = 0.04*7, 0.04
        imagesurface = cairo.ImageSurface(cairo.FORMAT_ARGB32,  larg, int(h/w*larg))#cairo.FORMAT_ARGB32,cairo.FORMAT_RGB24
        ctx = cairo.Context(imagesurface)
        ctx.scale(larg/w, larg/w) 
        draw_cairo_prj.DrawPeriodes(ctx, (0,0,w,h), self.projet.position, 
                                    self.projet.GetReferentiel().periodes ,
                                    self.projet.GetReferentiel().projets)

        bmp = wx.lib.wxcairo.BitmapFromImageSurface(imagesurface)
        
        # On fait une copie sinon éa s'efface ...
        img = bmp.ConvertToImage()
        bmp = img.ConvertToBitmap()

        return bmp
         
    
    #############################################################################            
    def onChanged(self, evt):
        self.projet.SetPosition(evt.EventObject.GetValue())
#        self.SetBitmapPosition()
        
        
        
    #############################################################################            
    def SetBitmapPosition(self, bougerSlider = None):
        self.sendEvent(modif = u"Changement de position du projet",
                       obj = self.projet)
        self.bmp.SetBitmap(self.getBitmapPeriode(250))
        if bougerSlider != None:
            self.position.SetValue(bougerSlider)

        
    #############################################################################            
    def EvtVariable(self, event):
        var = event.GetVar()
        if var == self.nbrParties:
            self.projet.nbrParties = var.v[0]
        elif var == self.annee:
            self.projet.annee = var.v[0]
            self.ctrlAnnee.unite.SetLabel(str(self.projet.annee+1)) 
        self.Refresh()
            
              
    #############################################################################            
    def EvtText(self, event):
        if event.GetEventObject() == self.textctrl:
            nt = event.GetString()
            if nt == u"":
                nt = self.projet.support.nom
            self.projet.SetText(nt)
            self.textctrl.ChangeValue(nt)
            maj = True
            
        elif 'ORI' in self.pages.keys() and event.GetEventObject() == self.pages['ORI'][1]:
            self.projet.origine = event.GetString()
            maj = False
            
        elif 'CCF' in self.pages.keys() and event.GetEventObject() == self.pages['CCF'][1]:
            self.projet.contraintes = event.GetString()
            maj = False
            
        elif 'OBJ' in self.pages.keys() and event.GetEventObject() == self.pages['OBJ'][1]:
            self.projet.production = event.GetString()
            maj = False
            
        elif 'SYN' in self.pages.keys() and event.GetEventObject() == self.pages['SYN'][1]:
            self.projet.synoptique = event.GetString()
            maj = False
        
        elif hasattr(self, 'intctrl') and event.GetEventObject() == self.intctrl:
            self.projet.intituleParties = event.GetString()
            maj = False
        
        elif hasattr(self, 'enonctrl') and event.GetEventObject() == self.enonctrl:
            self.projet.besoinParties = event.GetString()
            maj = False
            
        elif event.GetEventObject() == self.commctrl:
            self.projet.SetProblematique(event.GetString())
            maj = True
            
        elif 'PAR' in self.parctrl.keys() and event.GetEventObject() == self.parctrl['PAR']:
            self.projet.partenariat = event.GetString()
            maj = False
            
        elif 'PRX' in self.parctrl.keys() and event.GetEventObject() == self.parctrl['PRX']:
            self.projet.montant = event.GetString()
            maj = False
            
        elif 'SRC' in self.parctrl.keys() and event.GetEventObject() == self.parctrl['SRC']:
            self.projet.src_finance = event.GetString()
            maj = False
        
#        else:
#            maj = False
            
            
        if not self.eventAttente:
            wx.CallLater(DELAY, self.sendEvent, 
                         modif = u"Modification des propriétés du projet",
                         draw = maj)
            self.eventAttente = True

  
    #############################################################################            
    def EvtCheckListBox(self, event):
        index = event.GetSelection()
#        label = self.lb.GetString(index)
        if self.lb.IsChecked(index):
            if not index in self.projet.typologie:
                self.projet.typologie.append(index)
        else:
            if index in self.projet.typologie:
                self.projet.typologie.remove(index)
#        self.lb.SetSelection(index)    # so that (un)checking also selects (moves the highlight)
        print "typologie", self.projet.typologie
        
            
    #############################################################################            
    def MiseAJourTypeEnseignement(self, sendEvt = False):
        
        ref = self.projet.GetProjetRef()
#        print "MiseAJourTypeEnseignement", ref.code
        
        
        #
        # Page "Généralités"
        #
        self.titre.SetLabel(ref.attributs['TIT'][0])
        
        self.tit_pb.SetLabel(ref.attributs['PB'][0])
        self.commctrl.SetToolTipString(ref.attributs['PB'][1] + constantes.TIP_PB_LIMITE)
        
        self.MiseAJourPosition()
        self.panelOrga.MiseAJourListe()
        
        
        #
        # Pages simples
        #
        for k in ['ORI', 'CCF', 'OBJ', 'SYN']:
            if ref.attributs[k][0] != u"":
                if not k in self.pages.keys():
                    self.pages[k] = self.creerPageSimple(self.EvtText)
                self.nb.SetPageText(self.GetPageNum(self.pages[k][0]), ref.attributs[k][0])
                self.pages[k][1].SetToolTipString(ref.attributs[k][1])
            else:
                if k in self.pages.keys():
                    self.nb.DeletePage(self.GetPageNum(self.pages[k][0]))
                    del self.pages[k]
                
                    
        #
        # Pages spéciales
        #       
        
        # La page "sous parties" ('DEC')
        
        if ref.attributs['DEC'][0] != "":
            if not 'DEC' in self.pages.keys():
                self.pages['DEC'] = PanelPropriete(self.nb)
                bg_color = self.Parent.GetBackgroundColour()
                self.pages['DEC'].SetBackgroundColour(bg_color)
                
                self.nb.AddPage(self.pages['DEC'], ref.attributs['DEC'][0])
                
                self.nbrParties = Variable(u"Nombre de sous parties",  
                                           lstVal = self.projet.nbrParties, 
                                           typ = VAR_ENTIER_POS, bornes = [1,5])
                self.ctrlNbrParties = VariableCtrl(self.pages['DEC'], self.nbrParties, coef = 1, signeEgal = False,
                                        help = u"Nombre de sous parties", sizeh = 30)
                self.Bind(EVT_VAR_CTRL, self.EvtVariable, self.ctrlNbrParties)
                self.pages['DEC'].sizer.Add(self.ctrlNbrParties, (0,0), flag = wx.EXPAND|wx.ALL, border = 2)
                
                titreInt = wx.StaticBox(self.pages['DEC'], -1, u"Intitulés des différentes parties")
                sb = wx.StaticBoxSizer(titreInt)
                
                self.intctrl = wx.TextCtrl(self.pages['DEC'], -1, u"", style=wx.TE_MULTILINE)
                self.intctrl.SetToolTipString(u"Intitulés des parties du projet confiées à chaque groupe.\n" \
                                              u"Les groupes d'élèves sont désignés par des lettres (A, B, C, ...)\n" \
                                              u"et leur effectif est indiqué.")
                self.pages['DEC'].Bind(wx.EVT_TEXT, self.EvtText, self.intctrl)
                sb.Add(self.intctrl, 1, flag = wx.EXPAND)
                self.pages['DEC'].sizer.Add(sb, (1,0), flag = wx.EXPAND|wx.ALL, border = 2)
                
                titreInt = wx.StaticBox(self.pages['DEC'], -1, u"Enoncés du besoin des différentes parties du projet")
                sb = wx.StaticBoxSizer(titreInt)
                self.enonctrl = wx.TextCtrl(self.pages['DEC'], -1, u"", style=wx.TE_MULTILINE)
                self.enonctrl.SetToolTipString(u"Enoncés du besoin des parties du projet confiées à chaque groupe")
                self.pages['DEC'].Bind(wx.EVT_TEXT, self.EvtText, self.enonctrl)
                sb.Add(self.enonctrl, 1, flag = wx.EXPAND)
                self.pages['DEC'].sizer.Add(sb, (0,1), (2,1), flag = wx.EXPAND|wx.ALL, border = 2)
                
                self.pages['DEC'].sizer.AddGrowableCol(1)
                self.pages['DEC'].sizer.AddGrowableRow(1)  
                self.pages['DEC'].sizer.Layout()
                
        else:
            if 'DEC' in self.pages.keys():
                self.nb.DeletePage(self.GetPageNum(self.pages['DEC']))
                del self.pages['DEC']
        
        
        # La page "typologie" ('TYP')
        
        if ref.attributs['TYP'][0] != "":
            if not 'TYP' in self.pages.keys():
                self.pages['TYP'] = PanelPropriete(self.nb)
                bg_color = self.Parent.GetBackgroundColour()
                self.pages['TYP'].SetBackgroundColour(bg_color)
                
                self.nb.AddPage(self.pages['TYP'], ref.attributs['TYP'][0])
                
                liste = ref.attributs['TYP'][2].split(u"\n")
                self.lb = wx.CheckListBox(self.pages['TYP'], -1, (80, 50), wx.DefaultSize, liste)
                self.Bind(wx.EVT_CHECKLISTBOX, self.EvtCheckListBox, self.lb)
                
                self.pages['TYP'].sizer.Add(self.lb, (0,0), flag = wx.EXPAND|wx.ALL, border = 2)
                
                self.pages['TYP'].sizer.AddGrowableCol(0)
                self.pages['TYP'].sizer.AddGrowableRow(0)  
                self.pages['TYP'].sizer.Layout()
                
        else:
            if 'TYP' in self.pages.keys():
                self.nb.DeletePage(self.GetPageNum(self.pages['TYP']))
                del self.pages['TYP']
        
        # La page "Partenariat" ('PAR')
        
        if ref.attributs['PAR'][0] != "":
            if not 'PAR' in self.pages.keys():
                self.parctrl = {}
                self.pages['PAR'] = PanelPropriete(self.nb)
                bg_color = self.Parent.GetBackgroundColour()
                self.pages['PAR'].SetBackgroundColour(bg_color)
                
                self.nb.AddPage(self.pages['PAR'], ref.attributs['PAR'][0])
                
                for i, k in enumerate(['PAR', 'PRX', 'SRC']):
                    titreInt = wx.StaticBox(self.pages['PAR'], -1, ref.attributs[k][0])
                    sb = wx.StaticBoxSizer(titreInt)
                
                    self.parctrl[k] = wx.TextCtrl(self.pages['PAR'], -1, u"", style=wx.TE_MULTILINE)
                    self.parctrl[k].SetToolTipString(ref.attributs[k][1])
                    self.pages['PAR'].Bind(wx.EVT_TEXT, self.EvtText, self.parctrl[k])
                    sb.Add(self.parctrl[k], 1, flag = wx.EXPAND)
                    self.pages['PAR'].sizer.Add(sb, (0,i), flag = wx.EXPAND|wx.ALL, border = 2)
                
                self.pages['PAR'].sizer.AddGrowableCol(0)
                self.pages['PAR'].sizer.AddGrowableRow(0)  
                self.pages['PAR'].sizer.Layout()
                
        else:
            if 'PAR' in self.pages.keys():
                self.nb.DeletePage(self.GetPageNum(self.pages['PAR']))
                del self.pages['PAR']
                self.parctrl = {}
        
    #############################################################################            
    def MiseAJourPosition(self, sendEvt = False):
        self.bmp.SetBitmap(self.getBitmapPeriode(250))
        self.position.SetRange(0, self.projet.GetLastPosition())
        self.position.SetValue(self.projet.position)
    

    #############################################################################            
    def MiseAJour(self, sendEvt = False):
#        print "mise à jour panel table"
        ref = self.projet.GetProjetRef()
        
        # La page "Généralités"
        self.textctrl.ChangeValue(self.projet.intitule)
        self.commctrl.ChangeValue(self.projet.problematique)
        
        # Les pages simples
        if 'ORI' in self.pages.keys():
            self.pages['ORI'][1].ChangeValue(self.projet.origine)
        if 'CCF' in self.pages.keys():
            self.pages['CCF'][1].ChangeValue(self.projet.contraintes)
        if 'OBJ' in self.pages.keys():
            self.pages['OBJ'][1].ChangeValue(self.projet.production)
        if 'SYN' in self.pages.keys():
            self.pages['SYN'][1].ChangeValue(self.projet.synoptique)
        
        # La page "typologie" ('TYP')
        if ref.attributs['TYP'][0] != "":
            for t in self.projet.typologie:
                self.lb.Check(t)
                
        # La page "sous parties" ('DEC')
        if ref.attributs['DEC'][0] != "":
            self.intctrl.ChangeValue(self.projet.intituleParties)
            self.enonctrl.ChangeValue(self.projet.besoinParties)
            self.nbrParties.v[0] = self.projet.nbrParties
            self.ctrlNbrParties.mofifierValeursSsEvt()
        
        # La page "Partenariat" ('PAR')
        if ref.attributs['PAR'][0] != "":
            self.parctrl['PAR'].ChangeValue(self.projet.partenariat)
            self.parctrl['PRX'].ChangeValue(self.projet.montant)
            self.parctrl['SRC'].ChangeValue(self.projet.src_finance)
                    
        self.MiseAJourPosition()
     
        self.panelOrga.MiseAJourListe()
        self.Layout()
        
        if sendEvt:
            self.sendEvent()


    #############################################################################            
    def GetDocument(self):
        return self.projet


    ######################################################################################  
    def Verrouiller(self, etat):
        self.position.Enable(etat)
        
        
    
class PanelOrganisation(wx.Panel):    
    def __init__(self, parent, panel, objet):
        wx.Panel.__init__(self, parent, -1)
        self.objet = objet
        self.parent = panel
        
        sizer = wx.BoxSizer()
        gbsizer = wx.GridBagSizer()
        titre = wx.StaticBox(self, -1, u"Organisation")
        sb = wx.StaticBoxSizer(titre, wx.VERTICAL)

        self.nbrRevues = Variable(u"Nombre de revues",  
                                   lstVal = self.objet.nbrRevues, 
                                   typ = VAR_ENTIER_POS, bornes = [2,3])
        self.ctrlNbrRevues = VariableCtrl(self, self.nbrRevues, coef = 1, signeEgal = False,
                                help = u"Nombre de revues de projet (avec évaluation)", sizeh = 30)
        self.Bind(EVT_VAR_CTRL, self.EvtVariable, self.ctrlNbrRevues)
        gbsizer.Add(self.ctrlNbrRevues, (0,0), (1,2), flag = wx.EXPAND)
        
        liste = wx.ListBox(self, -1, choices = self.objet.GetListeNomsPhases(), style = wx.LB_SINGLE)
        liste.SetToolTipString(u"Séléctionner la revue à déplacer")
        gbsizer.Add(liste, (1,0), (2,1), flag = wx.EXPAND)
        self.liste = liste
        self.Bind(wx.EVT_LISTBOX, self.EvtListBox, self.liste)
        
        buttonUp = wx.BitmapButton(self, 11, wx.ArtProvider.GetBitmap(wx.ART_GO_UP), size = (20,20))
        gbsizer.Add(buttonUp, (1,1), (1,1))
        self.Bind(wx.EVT_BUTTON, self.OnClick, buttonUp)
        buttonUp.SetToolTipString(u"Monter la revue")
        self.buttonUp = buttonUp
        
        buttonDown = wx.BitmapButton(self, 12, wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN), size = (20,20))
        gbsizer.Add(buttonDown, (2,1), (1,1))
        self.Bind(wx.EVT_BUTTON, self.OnClick, buttonDown)
        buttonDown.SetToolTipString(u"Descendre la revue")
        self.buttonDown = buttonDown
        
        gbsizer.AddGrowableRow(1)
        sb.Add(gbsizer, flag = wx.EXPAND)
        
        sizer.Add(sb, flag = wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()
        
    
        
        
    #############################################################################            
    def EvtListBox(self, event):
        ref = self.objet.GetProjetRef()
        if ref.getClefDic('phases', self.liste.GetString(event.GetSelection()), 0) in TOUTES_REVUES_EVAL:
            self.buttonUp.Enable(True)
            self.buttonDown.Enable(True)
        else:
            self.buttonUp.Enable(False)
            self.buttonDown.Enable(False)
            
            
        
    #############################################################################            
    def OnClick(self, event):
        """ Déplacement de la revue sélectionnée
            vers le haut ou vers le bas
        """
        i = event.GetId()
        revue = self.liste.GetStringSelection()
        ref = self.objet.GetProjetRef()
        
        if revue[:5] == "Revue":
            posRevue = self.liste.GetSelection()
            numRevue = eval(revue[-1])
            if i == 11 and posRevue-2 >= 0:
                nouvPosRevue = posRevue-2   # Montée
                monte = True
            elif i == 12 and posRevue < self.liste.GetCount() - 1:
                nouvPosRevue = posRevue+1   # Descente
                monte = False
            else:
                return
            itemPrecedent = ref.getClefDic('phases', self.liste.GetString(nouvPosRevue), 0)
#            itemPrecedent = constantes.getCodeNomCourt(self.liste.'(nouvPosRevue), 
#                                                       self.objet.GetTypeEnseignement(simple = True))
            j=1
            while itemPrecedent in TOUTES_REVUES_EVAL:
                itemPrecedent = ref.getClefDic('phases', self.liste.GetString(nouvPosRevue-j), 0)
#                itemPrecedent = constantes.getCodeNomCourt(self.liste.GetString(nouvPosRevue-j),
#                                                           self.objet.GetTypeEnseignement(simple = True))
                j += 1
            self.objet.positionRevues[numRevue-1] = itemPrecedent
        else:
            return
          
        self.MiseAJourListe()
        self.liste.SetStringSelection(revue)
        if hasattr(self.objet, 'OrdonnerTaches'):
            self.objet.OrdonnerTaches()
            if monte:
                self.objet.VerifierIndicRevue(numRevue)
            self.parent.sendEvent(modif = u"Déplacement de la revue",
                                  obj = self.objet)
        
    #############################################################################            
    def MiseAJourListe(self):
#        print "MiseAJourListe"
#        print self.objet.GetListeNomsPhases()
        prj = self.objet.GetProjetRef()
        self.ctrlNbrRevues.redefBornes([min(prj.posRevues.keys()), max(prj.posRevues.keys())])
        self.ctrlNbrRevues.setValeur(prj.getNbrRevuesDefaut())
        self.liste.Set(self.objet.GetListeNomsPhases())
        self.Layout()
        
    #############################################################################            
    def EvtVariable(self, event):
        var = event.GetVar()
        if var == self.nbrRevues:
            if var.v[0] != self.objet.nbrRevues:
                self.objet.nbrRevues = var.v[0]
                self.objet.MiseAJourNbrRevues()
                self.MiseAJourListe()
                self.parent.sendEvent(modif = u"Modification du nombre de revues",
                                      obj = self.objet)



####################################################################################
#
#   Classe définissant le panel de propriété de la classe
#
####################################################################################
class PanelPropriete_Classe(PanelPropriete):
    def __init__(self, parent, classe, pourProjet, ouverture = False, typedoc = ''):
#        print "__init__ PanelPropriete_Classe"
        PanelPropriete.__init__(self, parent)
#        self.BeginRepositioningChildren()
        
        #
        # La page "Généralités"
        #
        nb = wx.Notebook(self, -1,  style= wx.BK_DEFAULT)
        pageGen = PanelPropriete(nb)
        bg_color = self.Parent.GetBackgroundColour()
        pageGen.SetBackgroundColour(bg_color)
        self.pageGen = pageGen
        
        nb.AddPage(pageGen, u"Propriétés générales")


        #
        # la page "Systémes"
        #
        pageSys = PanelPropriete(nb)
        pageSys.SetBackgroundColour(bg_color)
        nb.AddPage(pageSys, u"Systémes techniques et Matériel")
        self.pageSys = pageSys
        
        self.sizer.Add(nb, (0,1), (2,1), flag = wx.ALL|wx.ALIGN_RIGHT|wx.EXPAND, border = 1)
        self.nb = nb
        self.sizer.AddGrowableCol(1)

        self.classe = classe
        self.pasVerrouille = True


        #
        # La barre d'outils
        #
        self.tb = tb = wx.ToolBar(self, style = wx.TB_VERTICAL|wx.TB_FLAT|wx.TB_NODIVIDER)
        self.sizer.Add(tb, (0,0), (2,1), flag = wx.ALL|wx.ALIGN_RIGHT, border = 1)
        t = u"Sauvegarder ces paramétres de classe dans un fichier :\n" \
            u" - type d'enseignement\n" \
            u" - effectifs\n" \
            u" - établissement\n"
        if typedoc == 'seq':
            t += u" - systèmes\n"
        elif typedoc == 'prj':
            t += u" - nombre de revues et positions\n"
    
        tsize = (24,24)
        open_bmp = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR, tsize)
        save_bmp =  wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR, tsize)
        
        tb.AddSimpleTool(30, open_bmp, u"Ouvrir un fichier classe")
        self.Bind(wx.EVT_TOOL, self.commandeOuvrir, id=30)
        
        tb.AddSimpleTool(32, save_bmp, t)
        self.Bind(wx.EVT_TOOL, self.commandeSauve, id=32)
        
        tb.AddSimpleTool(31, images.Icone_defaut_pref.GetBitmap(), 
                         u"Rétablir les paramétres de classe par défaut")
        self.Bind(wx.EVT_TOOL, self.OnDefautPref, id=31)

        tb.Realize()


        #
        # Type d'enseignement
        #
        self.pourProjet = pourProjet
        titre = wx.StaticBox(pageGen, -1, u"Type d'enseignement")
        titre.SetMinSize((180, 100))
        sb = wx.StaticBoxSizer(titre, wx.VERTICAL)
        te = ArbreTypeEnseignement(pageGen, self)
        self.st_type = wx.StaticText(pageGen, -1, "")
        self.st_type.Show(False)
        sb.Add(te, 1, flag = wx.EXPAND)
        sb.Add(self.st_type, 1, flag = wx.EXPAND)
#        l = []
#        for i, e in enumerate(REFERENTIELS.keys()):
#            l.append(REFERENTIELS[e].Enseignement[0])
#        rb = wx.RadioBox(
#                pageGen, -1, u"Type d'enseignement", wx.DefaultPosition, (130,-1),
#                l,
#                1, wx.RA_SPECIFY_COLS
#                )
#        rb.SetToolTip(wx.ToolTip(u"Choisir le type d'enseignement"))
#        for i, e in enumerate(REFERENTIELS.keys()):
#            rb.SetItemToolTip(i, REFERENTIELS[e].Enseignement[1])
        pageGen.Bind(wx.EVT_RADIOBUTTON, self.EvtRadioBox, te)
 
        te.SetStringSelection(REFERENTIELS[constantes.TYPE_ENSEIGNEMENT_DEFAUT].Enseignement[0])

        pageGen.sizer.Add(sb, (0,1), (2,1), flag = wx.EXPAND|wx.ALL, border = 2)#
        self.cb_type = te

        #
        # Etablissement
        #
        titre = wx.StaticBox(pageGen, -1, u"Etablissement")
        sb = wx.StaticBoxSizer(titre, wx.VERTICAL)
        sh = wx.BoxSizer(wx.HORIZONTAL)
        t = wx.StaticText(pageGen, -1, u"Académie :")
        sh.Add(t, flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        
        lstAcad = sorted([a[0] for a in constantes.ETABLISSEMENTS.values()])
        self.cba = wx.ComboBox(pageGen, -1, u"sélectionner une académie ...", (-1,-1), 
                         (-1, -1), lstAcad+[u""],
                         wx.CB_DROPDOWN
                         |wx.CB_READONLY
                         #| wx.TE_PROCESS_ENTER
                         #| wx.CB_SORT
                         )

        pageGen.Bind(wx.EVT_COMBOBOX, self.EvtComboAcad, self.cba)
        pageGen.Bind(wx.EVT_TEXT, self.EvtComboAcad, self.cba)
        sh.Add(self.cba, flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.LEFT, border = 5)
        sb.Add(sh, flag = wx.EXPAND)
        
        sh = wx.BoxSizer(wx.HORIZONTAL)
        t = wx.StaticText(pageGen, -1, u"Ville :")
        sh.Add(t, flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
     
        self.cbv = wx.ComboBox(pageGen, -1, u"sélectionner une ville ...", (-1,-1), 
                         (-1, -1), [],
                         wx.CB_DROPDOWN
                         |wx.CB_READONLY
                         #| wx.TE_PROCESS_ENTER
                         #| wx.CB_SORT
                         )

        pageGen.Bind(wx.EVT_COMBOBOX, self.EvtComboVille, self.cbv)
        pageGen.Bind(wx.EVT_TEXT, self.EvtComboVille, self.cbv)
        sh.Add(self.cbv, flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.LEFT, border = 5)
        sb.Add(sh, flag = wx.EXPAND)
        
        t = wx.StaticText(pageGen, -1, u"Etablissement :")
        sb.Add(t, flag = wx.EXPAND)
        
        self.cbe = wx.ComboBox(pageGen, -1, u"sélectionner un établissement ...", (-1,-1), 
                         (-1, -1), [u"autre ..."],
                         wx.CB_DROPDOWN
                         |wx.CB_READONLY
                         #| wx.TE_PROCESS_ENTER
                         #| wx.CB_SORT
                         )

        pageGen.Bind(wx.EVT_COMBOBOX, self.EvtComboEtab, self.cbe)
        sb.Add(self.cbe, flag = wx.EXPAND)

#        textctrl = wx.TextCtrl(self, -1, u"", style=wx.TE_MULTILINE)
#        self.Bind(wx.EVT_TEXT, self.EvtText, textctrl)
##        textctrl.SetMinSize((-1, 150))
#        sb.Add(textctrl, 1, flag = wx.EXPAND)
#        self.textctrl = textctrl
        
#        self.info = wx.StaticText(self, -1, u"""Inscrire le nom de l'établissement dans le champ ci-dessus...
#        ou bien modifier le fichier "etablissements.txt"\n        pour le faire apparaitre dans la liste.""")
#        self.info.SetFont(wx.Font(8, wx.SWISS, wx.FONTSTYLE_ITALIC, wx.NORMAL))
#        sb.Add(self.info, 0, flag = wx.EXPAND|wx.ALL, border = 5)

        pageGen.sizer.Add(sb, (0,2), (1,1), flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT|wx.ALL|wx.EXPAND, border = 2)
        
        #
        # Accés au BO
        #
        titre = wx.StaticBox(pageGen, -1, u"Documents Officiels en ligne")
        self.bo = []
        sbBO = wx.StaticBoxSizer(titre, wx.VERTICAL)
        pageGen.sizer.Add(sbBO, (1,2), flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT|wx.ALL|wx.EXPAND, border = 2)
        self.sbBO = sbBO
#        self.SetLienBO()
        
        
        #
        # Effectifs
        #
        self.ec = PanelEffectifsClasse(pageGen, classe)
        pageGen.sizer.Add(self.ec, (0,3), (2,1), flag = wx.ALL|wx.EXPAND, border = 2)#|wx.ALIGN_RIGHT

        pageGen.sizer.AddGrowableRow(0)
        pageGen.sizer.AddGrowableCol(2)
#        pageGen.sizer.Layout()

        #
        # Systémes
        #
        self.btnAjouterSys = wx.Button(pageSys, -1, u"Ajouter un système")
        self.btnAjouterSys.SetToolTipString(u"Ajouter un nouveau système à la liste")
        self.Bind(wx.EVT_BUTTON, self.EvtButtonSyst, self.btnAjouterSys)
        
        self.lstSys = wx.ListBox(pageSys, -1,
                                 choices = [""], style = wx.LB_SINGLE | wx.LB_SORT)
        self.Bind(wx.EVT_LISTBOX, self.EvtListBoxSyst, self.lstSys)
        
        s = Systeme(self.classe, pageSys, "")
        self.panelSys = s.panelPropriete
        self.panelSys.Show()
    
        pageSys.sizer.Add(self.btnAjouterSys, (0,0), flag = wx.ALL|wx.EXPAND, border = 2)
        pageSys.sizer.Add(self.lstSys, (1,0), flag = wx.ALL|wx.EXPAND, border = 2)
        pageSys.sizer.Add(self.panelSys, (0,1), (2,1),  flag = wx.ALL|wx.EXPAND, border = 2)
        pageSys.sizer.AddGrowableRow(1)
        pageSys.sizer.AddGrowableCol(1)
    
        self.Bind(wx.EVT_SIZE, self.OnResize)
        
        self.Layout()
        
#        wx.CallAfter(self.cb_type.CollapseAll)
#        wx.CallAfter(self.Thaw)
        
        
    ######################################################################################              
    def OnResize(self, evt = None):
        self.nb.SetMinSize((-1,self.GetClientSize()[1]))
        self.Layout()
        if evt:
            evt.Skip()
    

    ###############################################################################################
    def commandeOuvrir(self, event = None, nomFichier = None):
        mesFormats = constantes.FORMAT_FICHIER_CLASSE['cla'] + constantes.TOUS_FICHIER
  
        if nomFichier == None:
            dlg = wx.FileDialog(
                                self, message=u"Ouvrir une classe",
                                defaultFile = "",
                                wildcard = mesFormats,
                                style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
                                )

            if dlg.ShowModal() == wx.ID_OK:
                paths = dlg.GetPaths()
                nomFichier = paths[0]
            else:
                nomFichier = ''
            
            dlg.Destroy()
        if nomFichier != '':
            self.classe.ouvrir(nomFichier)
        
        self.sendEvent(modif = u"Ouverture d'une Classe",
                       obj = self.classe)
    
    ###############################################################################################
    def enregistrer(self, nomFichier):

        wx.BeginBusyCursor()
        fichier = file(nomFichier, 'w')
        
        # La classe
        classe = self.classe.getBranche()
        
        # La racine
        constantes.indent(classe)
        
        try:
#            ET.ElementTree(classe).write(fichier, encoding = SYSTEM_ENCODING)
            ET.ElementTree(classe).write(fichier, xml_declaration=False, encoding = SYSTEM_ENCODING)
        except IOError:
            messageErreur(None, u"Accés refusé", 
                                  u"L'accés au fichier %s a été refusé !\n\n"\
                                  u"Essayer de faire \"Enregistrer sous...\"" %nomFichier)
        except UnicodeDecodeError:
            messageErreur(None, u"Erreur d'encodage", 
                                  u"Un caractére spécial empéche l'enregistrement du fichier !\n\n"\
                                  u"Essayer de le localiser et de le supprimer.\n"\
                                  u"Merci de reporter cette erreur au développeur.")
            
        fichier.close()

        wx.EndBusyCursor()
        
    #############################################################################
    def commandeSauve(self, event):
        mesFormats = constantes.FORMAT_FICHIER_CLASSE['cla'] + constantes.TOUS_FICHIER
        dlg = wx.FileDialog(self, 
                            message = constantes.MESSAGE_ENR['cla'], 
                            defaultDir="" , 
                            defaultFile="", wildcard=mesFormats, 
                            style=wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR
                            )
        dlg.SetFilterIndex(0)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            dlg.Destroy()
            self.enregistrer(path)
            self.DossierSauvegarde = os.path.split(path)[0]
        else:
            dlg.Destroy()
            
    
        
    #############################################################################            
    def OnDefautPref(self, evt):
#        self.classe.options.defaut()
        self.classe.Initialise(isinstance(self.classe.doc, Projet), defaut = True)
#        self.classe.doc.AjouterListeSystemes(self.classe.systemes)
        self.MiseAJour()
        self.sendEvent(modif = u"Réinitialisation des paramètres de Classe",
                       obj = self.classe)
        
        
#    #############################################################################            
#    def OnValidPref(self, evt):
#        try:
#            self.classe.options.valider(self.classe, self.classe.doc)
#            self.classe.options.enregistrer()
#        except IOError:
#            messageErreur(self, u"Permission refusée",
#                          u"Permission d'enregistrer les préférences refusée.\n\n" \
#                          u"Le dossier est protégé en écriture")
#        except:
#            messageErreur(self, u"Enregistrement impossible",
#                          u"Imposible d'enregistrer les préférences\n\n")
#        return   
        
        
    #############################################################################            
    def GetDocument(self):
        return self.classe.doc
    
    
#    #############################################################################            
#    def EvtText(self, event):
#        if event.GetEventObject() == self.textctrl:
#            self.classe.etablissement = event.GetString()
#            self.sendEvent()
            
            
    ######################################################################################  
    def EvtComboAcad(self, evt = None):
#        print "EvtComboAcad"
        if evt != None:
            self.classe.academie = evt.GetString()

        lst = []
        for val in constantes.ETABLISSEMENTS.values():
            if self.classe.academie == val[0]:
                if self.classe.GetReferentiel().getTypeEtab() == 'L':
                    lst = val[2]
                else:
                    lst = val[1]
                break
#        print "   ", lst
        if len(lst) > 0:
            lst = sorted(list(set([v for e, v in lst])))
#        print "Villes", lst

        self.cbv.Set(lst)
        self.cbv.Refresh()
            
    
    ######################################################################################  
    def EvtComboVille(self, evt = None):
#        print "EvtComboVille"
        if evt != None:
            self.classe.ville = evt.GetString()
#        print "   ", self.classe.ville
        lst = []
        for val in constantes.ETABLISSEMENTS.values():
            if self.classe.academie == val[0]:
                if self.classe.GetReferentiel().getTypeEtab() == 'L':
                    lst = val[2]
                else:
                    lst = val[1]
                break
#        print "   ", lst
        lst = sorted([e for e, v in lst if v == self.cbv.GetStringSelection()])
#        print "   ", self.cbv.GetStringSelection()
#        print "   Etab", lst
        
        self.cbe.Set(lst)
        self.cbe.Refresh()
            
        
    ######################################################################################  
    def EvtComboEtab(self, evt):       
#        if evt.GetSelection() == len(constantes.ETABLISSEMENTS_PDD):
#            self.classe.etablissement = self.textctrl.GetStringSelection()
#            self.AfficherAutre(True)
#        else:
        self.classe.etablissement = evt.GetString()
#        self.AfficherAutre(False)
        
        self.sendEvent(modif = u"Modification de l'établissement",
                       obj = self.classe)
     

    ######################################################################################  
    def EvtListBoxSyst(self, event = None):
        if event != None:
            n = event.GetSelection()
        else:
            n = 0
        if len(self.classe.systemes) > n:
#            s = self.classe.systemes[n]
            self.panelSys.SetSysteme(self.classe.systemes[n])
            
#            self.panelSys.systeme.setBranche(s.getBranche())


    ######################################################################################  
    def EvtButtonSyst(self, event = None):
#        print "EvtButtonSyst"
#        print self.classe.systemes
#        print self.panelSys.systeme
#        for n, s in enumerate(self.classe.systemes):
#            if s.nom == self.panelSys.systeme.nom:
##                print "  ---", n, s
#                self.classe.systemes.remove(s)
#                self.lstSys.Delete(n)
#                break

#        s = self.panelSys.systeme.Copie()
        s = Systeme(self.classe, None)
#        print "   +++", s
        self.lstSys.Append(s.nom)
        self.classe.systemes.append(s)
        self.classe.systemes.sort(key=attrgetter('nom'))
        self.lstSys.SetSelection(0)
        self.EvtListBoxSyst()
#        print "   >>>",self.classe.systemes


    ######################################################################################  
    def MiseAJourListeSys(self, nom = u""):
#        print "MiseAJourListeSys", nom, self.lstSys.GetSelection()
        if nom == u"":
            nom = u"Systéme sans nom"
            
        n = self.lstSys.GetSelection()
        if n != wx.NOT_FOUND:
            self.lstSys.SetString(n, nom)
            self.lstSys.SetSelection(self.lstSys.FindString(nom))


    ######################################################################################  
    def EvtRadioBox(self, event = None, CodeFam = None):
        """ Sélection d'un type d'enseignement
        """
        if event != None:
            radio_selected = event.GetEventObject()
            CodeFam = Referentiel.getEnseignementLabel(radio_selected.GetLabel())
        
        
#        fam = self.classe.familleEnseignement
        ancienRef = self.classe.referentiel
        ancienneFam = self.classe.familleEnseignement
        self.classe.typeEnseignement, self.classe.familleEnseignement = CodeFam
        self.classe.referentiel = REFERENTIELS[self.classe.typeEnseignement]
        
#        for c, e in [r.Enseignement[1:] for r in REFERENTIELS]constantes.Enseignement.items():
#            if e[0] == :
#                self.classe.typeEnseignement = c
#                self.classe.familleEnseignement = constantes.FamilleEnseignement[self.classe.typeEnseignement]
#                break
        
        self.classe.MiseAJourTypeEnseignement()
        self.classe.doc.MiseAJourTypeEnseignement(ancienRef, ancienneFam)
        self.classe.doc.SetPosition(self.classe.doc.position)
#        self.classe.doc.MiseAJourTypeEnseignement(fam != self.classe.familleEnseignement)
#        self.MiseAJourType()
#        if hasattr(self, 'list'):
#            self.list.Peupler()

        self.st_type.SetLabel(self.classe.referentiel.Enseignement[0])
        self.SetLienBO()
        
        self.Refresh()
        
        self.sendEvent(modif = u"Modification du type d'enseignement",
                       obj = self.classe)
        
    ######################################################################################  
    def SetLienBO(self):
        for b in self.bo:
            b.Destroy()
            
        self.bo = []
        for tit, url in REFERENTIELS[self.classe.typeEnseignement].BO_URL:
            self.bo.append(hl.HyperLinkCtrl(self.pageGen, wx.ID_ANY, tit, URL = url))
            self.sbBO.Add(self.bo[-1], flag = wx.EXPAND)
            self.bo[-1].Show(tit != u"")
            self.bo[-1].ToolTip.SetTip(url)
            
        self.pageGen.sizer.Layout()
        

        
    ######################################################################################  
    def MiseAJour(self):
#        print "MiseAJour panelPropriete classe"
#        self.MiseAJourType()
        
        self.cb_type.SetStringSelection(self.classe.referentiel.Enseignement[0])
        self.st_type.SetLabel(self.classe.referentiel.Enseignement[0])
#        self.cb_type.SetStringSelection(REFERENTIELS[self.classe.typeEnseignement].Enseignement[0])
        
        
        self.cba.SetValue(self.classe.academie)
        self.EvtComboAcad()
        self.cbv.SetValue(self.classe.ville)
        self.EvtComboVille()
        self.cbe.SetValue(self.classe.etablissement)
        
#        print "   ", self.classe.systemes
        
        self.lstSys.Set([])
        
        if len(self.classe.systemes) == 0:
            # On crée un système vide
            self.EvtButtonSyst()
#            print "   +++", self.classe.systemes
            self.EvtListBoxSyst()
            self.MiseAJourListeSys()
        else:
            self.lstSys.Set([s.nom for s in self.classe.systemes])
            self.lstSys.SetSelection(0)
            self.EvtListBoxSyst()
#        self.MiseAJourListeSys()
#        if self.cbe.GetStringSelection () and self.cbe.GetStringSelection() == self.classe.etablissement:
#            self.textctrl.ChangeValue(u"")
#            self.AfficherAutre(False)
            
#        else:
#            self.textctrl.ChangeValue(self.classe.etablissement)
#            self.AfficherAutre(True)
#            self.cbe.SetSelection(len(constantes.ETABLISSEMENTS))
        
        self.SetLienBO()
        
#        if hasattr(self, 'list'):
#            self.list.Peupler()
                
        self.ec.MiseAJour()

            
    #############################################################################            
    def OnAide(self, event):
        dlg = MessageAideCI(self)
        dlg.ShowModal()
        dlg.Destroy()

        
    ######################################################################################  
    def Verrouiller(self, etat):
        self.cb_type.Show(etat)
        self.st_type.Show(not etat)
        self.pasVerrouille = etat

        
    
          

#class ListeCI(ULC.UltimateListCtrl):
#    def __init__(self, parent, classe):
#        
#        self.typeEnseignement = classe.typeEnseignement
#        self.classe = classe
#        self.parent = parent
#        
#        style = wx.LC_REPORT| wx.BORDER_NONE| wx.LC_VRULES| wx.LC_HRULES| ULC.ULC_HAS_VARIABLE_ROW_HEIGHT
#        if not REFERENTIELS[self.typeEnseignement].CI_cible:
#            style = style |wx.LC_NO_HEADER
#            
#        ULC.UltimateListCtrl.__init__(self,parent, -1, 
#                                        agwStyle=style)
#                
#        info = ULC.UltimateListItem()
#        info._mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT
#        info._format = wx.LIST_FORMAT_LEFT
#        info._text = u"CI"
#         
#        self.InsertColumnInfo(0, info)
#
#        info = ULC.UltimateListItem()
#        info._format = wx.LIST_FORMAT_LEFT
#        info._mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT | ULC.ULC_MASK_FONT
#        info._text = u"Intitulé"
#        
#        self.InsertColumnInfo(1, info)
#        
#        self.SetColumnWidth(0, 35)
#        self.SetColumnWidth(1, -3)
#        
#        if REFERENTIELS[self.typeEnseignement].CI_cible:
#            for i,p in enumerate(['M', 'E', 'I', 'F', 'S', 'C']):
#                info = ULC.UltimateListItem()
#                info._mask = wx.LIST_MASK_TEXT
#                info._format = wx.LIST_FORMAT_CENTER
#                info._text = p
#                
#                self.InsertColumnInfo(i+2, info)
#                self.SetColumnWidth(i+2, 20)
#        
#        self.Peupler()
#                
#    ######################################################################################  
#    def Peupler(self):
##        print "PeuplerListe"
#        # Peuplement de la liste
#        self.DeleteAllItems()
#        l = self.classe.CI
#        
##        if self.typeEnseignement != "SSI":
##            l = self.classe.ci_ET
##        else:
##            l = self.classe.ci_SSI
#            
#        for i,ci in enumerate(l):
#            index = self.InsertStringItem(sys.maxint, "CI"+str(i+1))
#            self.SetStringItem(index, 1, ci)
#           
#            if REFERENTIELS[self.typeEnseignement].CI_cible:
#                for j,p in enumerate(['M', 'E', 'I', 'F', 'S', 'C']):
#                    item = self.GetItem(i, j+2)
#                    cb = wx.CheckBox(self, 100+i, u"", name = p)
#                    cb.SetValue(p in self.classe.posCI[i])
#                    self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, cb)
#                    item.SetWindow(cb)
#                    self.SetItem(item)
#        self.Update()
#        
#    ######################################################################################  
#    def EvtCheckBox(self, event):
#        self.parent.EvtCheckBox(event)
    
####################################################################################
#
#   Editeur pour les listes de CI
#
####################################################################################   
class Editeur(wx.Frame):  
    def __init__(self, classe, liste, index, texte, pos, size):
        wx.Frame.__init__(self, None, -1, pos = pos, 
                          size = size, style = wx.BORDER_NONE)
        self.index = index
        self.liste = liste
        self.classe = classe
        txt = wx.TextCtrl(self, -1, texte, size = size)
        txt.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
#        self.Bind(wx.EVT_TEXT_ENTER, self.OnKillFocus, txt)
        self.Fit()
        
    def OnKillFocus(self, evt):
        txtctrl = evt.GetEventObject()
        self.liste.SetStringItem(self.index, 1, txtctrl.GetValue())
        
        self.classe.SetCI(self.index, txtctrl.GetValue())
#        self.classe.doc.CI.
        self.classe.doc.CI.panelPropriete.construire()
        self.Destroy() 
        evt.Skip()
        return
    
        
        
####################################################################################
#
#   Classe définissant le panel de réglage des effectifs
#
####################################################################################     
class PanelEffectifsClasse(wx.Panel):
    """ Classe définissant le panel de réglage des effectifs
    
        Rappel :
        listeEffectifs = ["C", "G", "D" ,"E" ,"P"]
        NbrGroupes = {"G" : 2, # Par classe
                      "E" : 2, # Par grp Eff réduit
                      "P" : 4, # Par grp Eff réduit
                      }
                      
    """
    def __init__(self, parent, classe):
        wx.Panel.__init__(self, parent, -1)
        self.classe = classe
        
        #
        # Box "Classe"
        #
        boxClasse = wx.StaticBox(self, -1, u"Découpage de la classe")

        coulClasse = constantes.GetCouleurWx(constantes.CouleursGroupes['C'])
#        boxClasse.SetOwnForegroundColour(coulClasse)
        
        self.coulEffRed = constantes.GetCouleurWx(constantes.CouleursGroupes['G'])

        self.coulEP = constantes.GetCouleurWx(constantes.CouleursGroupes['E'])
    
        self.coulAP = constantes.GetCouleurWx(constantes.CouleursGroupes['P'])
        
#        self.boxClasse = boxClasse
        bsizerClasse = wx.StaticBoxSizer(boxClasse, wx.VERTICAL)
        sizerClasse_h = wx.BoxSizer(wx.HORIZONTAL)
        sizerClasse_b = wx.BoxSizer(wx.HORIZONTAL)
        self.sizerClasse_b = sizerClasse_b
        bsizerClasse.Add(sizerClasse_h)
        bsizerClasse.Add(sizerClasse_b)
        
        # Effectif de la classe
        self.vEffClas = Variable(u"Nombre d'élèves",  
                            lstVal = classe.effectifs['C'], 
                            typ = VAR_ENTIER_POS, bornes = [4,40])
        self.cEffClas = VariableCtrl(self, self.vEffClas, coef = 1, signeEgal = False,
                                help = u"Nombre d'élèves dans la classe entiére", sizeh = 30, color = coulClasse)
        self.Bind(EVT_VAR_CTRL, self.EvtVariableEff, self.cEffClas)
        sizerClasse_h.Add(self.cEffClas, 0, wx.TOP|wx.BOTTOM|wx.LEFT, 5)
        
        # Nombre de groupes à effectif réduits
        self.vNbERed = Variable(u"Nbr de groupes\né effectif réduit",  
                                lstVal = classe.nbrGroupes['G'], 
                                typ = VAR_ENTIER_POS, bornes = [1,4])
        self.cNbERed = VariableCtrl(self, self.vNbERed, coef = 1, signeEgal = False,
                                    help = u"Nombre de groupes à effectif réduit dans la classe", sizeh = 20, color = self.coulEffRed)
        self.Bind(EVT_VAR_CTRL, self.EvtVariableEff, self.cNbERed)
        sizerClasse_h.Add(self.cNbERed, 0, wx.TOP|wx.LEFT, 5)
        
        
        #
        # Boxes Effectif Réduit
        #
        boxEffRed = wx.StaticBox(self, -1, u"")
        boxEffRed.SetOwnForegroundColour(self.coulEffRed)
        self.boxEffRed = boxEffRed
        bsizerEffRed = wx.StaticBoxSizer(boxEffRed, wx.HORIZONTAL)
        self.sizerEffRed_g = wx.BoxSizer(wx.VERTICAL)
        self.sizerEffRed_d = wx.BoxSizer(wx.VERTICAL)
        bsizerEffRed.Add(self.sizerEffRed_g, flag = wx.EXPAND)
        bsizerEffRed.Add(wx.StaticLine(self, -1, style = wx.VERTICAL), flag = wx.EXPAND)
        bsizerEffRed.Add(self.sizerEffRed_d, flag = wx.EXPAND)
        sizerClasse_b.Add(bsizerEffRed)
        
        # Nombre de groupes d'étude/projet
        self.vNbEtPr = Variable(u"Nbr de groupes\n\"Etudes et Projets\"",  
                            lstVal = classe.nbrGroupes['E'], 
                            typ = VAR_ENTIER_POS, bornes = [1,10])
        self.cNbEtPr = VariableCtrl(self, self.vNbEtPr, coef = 1, signeEgal = False,
                                help = u"Nombre de groupes d'étude/projet par groupe à effectif réduit", sizeh = 20, color = self.coulEP)
        self.Bind(EVT_VAR_CTRL, self.EvtVariableEff, self.cNbEtPr)
        self.sizerEffRed_g.Add(self.cNbEtPr, 0, wx.TOP|wx.BOTTOM|wx.LEFT, 3)
        
#        self.BoxEP = wx.StaticBox(self, -1, u"", size = (30, -1))
#        self.BoxEP.SetOwnForegroundColour(self.coulEP)
#        self.BoxEP.SetMinSize((30, -1))     
#        bsizer = wx.StaticBoxSizer(self.BoxEP, wx.VERTICAL)
#        self.sizerEffRed_g.Add(bsizer, flag = wx.EXPAND|wx.LEFT|wx.RIGHT, border = 5)
            
        # Nombre de groupes d'activité pratique
        self.vNbActP = Variable(u"Nbr de groupes\n\"Activités pratiques\"",  
                            lstVal = classe.nbrGroupes['P'], 
                            typ = VAR_ENTIER_POS, bornes = [2,20])
        self.cNbActP = VariableCtrl(self, self.vNbActP, coef = 1, signeEgal = False,
                                help = u"Nombre de groupes d'activité pratique par groupe à effectif réduit", sizeh = 20, color = self.coulAP)
        self.Bind(EVT_VAR_CTRL, self.EvtVariableEff, self.cNbActP)
        self.sizerEffRed_d.Add(self.cNbActP, 0, wx.TOP|wx.BOTTOM|wx.LEFT, 3)
        
#        self.BoxAP = wx.StaticBox(self, -1, u"", size = (30, -1))
#        self.BoxAP.SetOwnForegroundColour(self.coulAP)
#        self.BoxAP.SetMinSize((30, -1))     
#        bsizer = wx.StaticBoxSizer(self.BoxAP, wx.VERTICAL)
#        self.sizerEffRed_d.Add(bsizer, flag = wx.EXPAND|wx.LEFT|wx.RIGHT, border = 5)
        
        
        self.lstBoxEffRed = []
        self.lstBoxEP = []
        self.lstBoxAP = []
        
#        self.AjouterGroupesVides()
        
        self.MiseAJourNbrEleve()

        border = wx.BoxSizer()
        border.Add(bsizerClasse, 1, wx.EXPAND)
        self.SetSizer(border)

    
    
    def EvtVariableEff(self, event):
        var = event.GetVar()
        if var == self.vEffClas:
            self.classe.effectifs['C'] = var.v[0]
        elif var == self.vNbERed:
            self.classe.nbrGroupes['G'] = var.v[0]
        elif var == self.vNbEtPr:
            self.classe.nbrGroupes['E'] = var.v[0]
        elif var == self.vNbActP:
            self.classe.nbrGroupes['P'] = var.v[0]
        calculerEffectifs(self.classe)
            
        self.Parent.sendEvent(self.classe, modif = u"Modification du découpage de la Classe",
                              obj = self.classe)
#        self.AjouterGroupesVides()
        self.MiseAJourNbrEleve()
        
#    def AjouterGroupesVides(self):
#        return
#        for g in self.lstBoxEP:
#            self.sizerEffRed_g.Remove(g)
#        for g in self.lstBoxAP:
#            self.sizerEffRed_d.Remove(g)    
#        for g in self.lstBoxEffRed:
#            self.sizerClasse_b.Remove(g)
#        
#        self.lstBoxEffRed = []
#        self.lstBoxEP = []
#        self.lstBoxAP = []    
#        
#        for g in range(self.classe.nbrGroupes['G'] - 1):
#            box = wx.StaticBox(self, -1, u"Eff Red", size = (30, -1))
#            box.SetOwnForegroundColour(self.coulEffRed)
#            box.SetMinSize((30, -1))
#            self.lstBoxEffRed.append(box)
#            bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
#            bsizer.Add(wx.Panel(self, -1, size = (20, -1)))
#            self.sizerClasse_b.Add(bsizer, flag = wx.EXPAND)
#        
#        for g in range(self.classe.nbrGroupes['E']):
#            box = wx.StaticBox(self, -1, u"E/P", size = (30, -1))
#            box.SetOwnForegroundColour(self.coulEP)
#            box.SetMinSize((30, -1))
#            self.lstBoxEP.append(box)
#            bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
##            bsizer.Add(wx.Panel(self, -1, size = (20, -1)))
#            self.sizerEffRed_g.Add(bsizer, flag = wx.EXPAND|wx.LEFT|wx.RIGHT, border = 5)
#            
#        
#        for g in range(self.classe.nbrGroupes['P']):
#            box = wx.StaticBox(self, -1, u"AP", size = (30, -1))
#            box.SetOwnForegroundColour(self.coulAP)
#            box.SetMinSize((30, -1))
#            self.lstBoxAP.append(box)
#            bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
##            bsizer.Add(wx.Panel(self, -1, size = (20, -1)))
#            self.sizerEffRed_d.Add(bsizer, flag = wx.EXPAND|wx.LEFT|wx.RIGHT, border = 5)
#        
#        self.Layout()
        
    
    def MiseAJourNbrEleve(self):
        self.boxEffRed.SetLabelText(strEffectifComplet(self.classe, 'G', -1))
#        t = u"groupes de "
#        self.BoxEP.SetLabelText(t+strEffectif(self.classe, 'E', -1))
#        self.BoxAP.SetLabelText(t+strEffectif(self.classe, 'P', -1))

#        self.Refresh()
        
        
    def MiseAJour(self):
        self.vEffClas.v[0] = self.classe.effectifs['C']
        self.vNbERed.v[0] = self.classe.nbrGroupes['G']
        self.vNbEtPr.v[0] = self.classe.nbrGroupes['E']
        self.vNbActP.v[0] = self.classe.nbrGroupes['P']
        
        self.cEffClas.mofifierValeursSsEvt()
        self.cNbERed.mofifierValeursSsEvt()
        self.cNbEtPr.mofifierValeursSsEvt()
        self.cNbActP.mofifierValeursSsEvt()
        
#        self.AjouterGroupesVides()
        self.MiseAJourNbrEleve()
        

        
        
####################################################################################
#
#   Classe définissant le panel de propriété du CI
#
####################################################################################
class PanelPropriete_CI(PanelPropriete):
    def __init__(self, parent, CI):
        PanelPropriete.__init__(self, parent)
        self.CI = CI       
        self.construire()
        

    #############################################################################            
    def GetDocument(self):
        return self.CI.parent
    
    ######################################################################################################
    def OnEnter(self, event):
        return
        
    #############################################################################            
    def construire(self):
        self.group_ctrls = []
        self.DestroyChildren()
        if hasattr(self, 'grid1'):
            self.sizer.Remove(self.grid1)
            
        #
        # Cas oé les CI sont sur une cible MEI
        #
        abrevCI = self.CI.parent.classe.referentiel.abrevCI
        if self.CI.GetReferentiel().CI_cible:
            self.panel_cible = Panel_Cible(self, self.CI)
            self.sizer.Add(self.panel_cible, (0,0), (2,1), flag = wx.EXPAND)
            
            self.grid1 = wx.FlexGridSizer( 0, 3, 0, 0 )
            self.grid1.AddGrowableCol(1)
            
            
#            for i, ci in enumerate(constantes.CentresInterets[self.CI.GetTypeEnseignement()]):
            for i, ci in enumerate(self.CI.parent.classe.referentiel.CentresInterets):
                r = wx.CheckBox(self, 200+i, "")
                t = wx.StaticText(self, -1, abrevCI+str(i+1)+" : "+ci)
                p = wx.TextCtrl(self, -1, u"1")
                p.SetToolTipString(u"Poids horaire relatif du "+abrevCI)
                p.Show(False)
                p.SetMinSize((30, -1))
                self.group_ctrls.append((r, t, p))
                self.grid1.Add( r, 0, wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 2 )
                self.grid1.Add( t, 0, wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.EXPAND, 5 )
                self.grid1.Add( p, 0, wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_RIGHT|wx.LEFT|wx.RIGHT, 5 )
            for radio, text, poids in self.group_ctrls:
                self.Bind(wx.EVT_CHECKBOX, self.OnCheck, radio )
                self.Bind(wx.EVT_TEXT, self.OnPoids, poids )
            self.sizer.Add(self.grid1, (0,1), (2,1), flag = wx.EXPAND)
            
            aide = wx.BitmapButton(self, -1, images.Bouton_Aide.GetBitmap())
            aide.SetToolTipString(u"Informations à propos de la cible "+abrevCI)
            self.sizer.Add(aide, (0,2), flag = wx.ALL, border = 2)
            self.Bind(wx.EVT_BUTTON, self.OnAide, aide )
            
            b = wx.ToggleButton(self, -1, "")
            b.SetValue(self.CI.max2CI)
            b.SetBitmap(images.Bouton_2CI.GetBitmap())
            b.SetToolTipString(u"Limite à 2 le nombre de "+abrevCI+" sélectionnables")
            self.sizer.Add(b, (1,2), flag = wx.ALL, border = 2)
#            b.SetSize((30,30)) # adjust default size for the bitmap
            b.SetInitialSize((32,32))
            self.b2CI = b
            self.Bind(wx.EVT_TOGGLEBUTTON, self.OnOption, b)
            if not self.sizer.IsColGrowable(1):
                self.sizer.AddGrowableCol(1)
            self.sizer.Layout()
        
        #
        # Cas oé les CI ne sont pas sur une cible
        #  
        else:
            
            self.grid1 = wx.FlexGridSizer( 0, 2, 0, 0 )
            
            for i, ci in enumerate(self.CI.parent.classe.referentiel.CentresInterets):
    #            if i == 0 : s = wx.RB_GROUP
    #            else: s = 0
                r = wx.CheckBox(self, 200+i, abrevCI+str(i+1), style = wx.RB_GROUP )
                t = wx.StaticText(self, -1, ci)
                self.grid1.Add( r, 0, wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 2 )
                self.grid1.Add( t, 0, wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT, 5 )
                self.group_ctrls.append((r, t))
            self.sizer.Add(self.grid1, (0,0), flag = wx.EXPAND)
            for radio, text in self.group_ctrls:
                self.Bind(wx.EVT_CHECKBOX, self.OnCheck, radio )
#            btn = wx.Button(self, -1, u"Effacer")
#            self.Bind(wx.EVT_BUTTON, self.OnClick, btn)
#            self.sizer.Add(btn, (0,1))
            
            self.sizer.Layout()
        
    #############################################################################            
    def OnAide(self, event):
        dlg = MessageAideCI(self)
        dlg.ShowModal()
        dlg.Destroy()

    #############################################################################            
    def OnOption(self, event):
        self.CI.max2CI = not self.CI.max2CI
        self.MiseAJour()
        
    #############################################################################            
    def OnPoids(self, event):
        pass
    
    #############################################################################            
    def OnCheck(self, event):
        button_selected = event.GetEventObject().GetId()-200 
        
        if event.GetEventObject().IsChecked():
            self.CI.AddNum(button_selected)
        else:
            self.CI.DelNum(button_selected)
        
        if len(self.group_ctrls[button_selected]) > 2:
            self.group_ctrls[button_selected][2].Show(event.GetEventObject().IsChecked())
        
#        self.panel_cible.bouton[button_selected].SetState(event.GetEventObject().IsChecked())
#        if self.CI.GetTypeEnseignement() == 'ET':
        if self.CI.GetReferentiel().CI_cible:
            self.panel_cible.GererBoutons(True)
        
            if hasattr(self, 'b2CI'):
                self.b2CI.Enable(len(self.CI.numCI) <= 2)
            
        self.Layout()
        self.sendEvent(modif = u"Modification du nombre de CI sélectionnables")
    
    #############################################################################            
    def MiseAJour(self, sendEvt = False):
#        if self.CI.GetTypeEnseignement() == 'ET':
        if self.CI.GetReferentiel().CI_cible:
            self.panel_cible.GererBoutons(True)
            if hasattr(self, 'b2CI'):
                self.b2CI.Enable(len(self.CI.numCI) <= 2)
        
        else:
            for i, num in enumerate(self.CI.numCI):
                self.group_ctrls[num][0].SetValue(True)
                if len(self.group_ctrls[num]) > 2:
                    self.group_ctrls[num][2].SetValue(self.CI.poids[i])
            self.Layout()
            
        if sendEvt:
            self.sendEvent()
            
#    #############################################################################            
#    def OnClick(self, event):
#        if self.CI.num != None:
#            self.group_ctrls[self.CI.num][0].SetValue(False)
#            self.CI.SetNum(None)
#            self.sendEvent()

    #############################################################################            
    def GererCases(self, liste, appuyer = False):
        """ Permet de cacher les cases des CI au fur et à mesure que l'on selectionne des CI
            <liste> : liste des CI à activer
        """ 
        for i, b in enumerate(self.group_ctrls):
            if i in liste:
                b[0].Enable(True)
            else:
                b[0].Enable(False)
                
        if appuyer:
            for i, b in enumerate(self.group_ctrls):
                b[0].SetValue(i in self.CI.numCI)
                
                    

####################################################################################
#
#   Classe définissant le panel conteneur de la Cible MEI
#
#################################################################################### 
class Panel_Cible(wx.Panel):
    def __init__(self, parent, CI):
        wx.Panel.__init__(self, parent, -1)
        self.CI = CI
        self.bouton = []
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.backGround = self.GetBackgroundColour()
        
#        rayons = [90,90,60,40,20,30,60,40,20,30,60,40,20,30,0]
#        angles = [-100,100,0,0,0,60,120,120,120,180,-120,-120,-120,-60,0]
        centre = [96, 88]
        
        rayons = {"F" : 60, 
                  "S" : 40, 
                  "C" : 20,
                  "_" : 90}
        angles = {"M" : 0,
                  "E" : 120,
                  "I" : -120,
                  "_" : -100}
        

        for i in range(len(self.CI.parent.classe.referentiel.CentresInterets)):
            mei, fsc = self.CI.parent.classe.referentiel.positions_CI[i].split("_")
            mei = mei.replace(" ", "")
            fsc = fsc.replace(" ", "")
            
            if len(fsc) == 0:
                ray = 0
            else:
                ray = 0
                for j in fsc:
                    ray += rayons[j]
                ray = ray/len(fsc)
            
            if len(mei) == 0:
                ray = rayons["_"]
                ang = angles["_"]
                angles["_"] = -angles["_"] # on inverse le coté pour pouvoir mettre 2 CI en orbite
            elif len(mei) == 3:
                ray = 0
                ang = 0
            elif len(mei) == 2:
                ang = (angles[mei[1]] + angles[mei[0]])/2
                if ang == 0:
                    ang = 180
                
            else:
                ang = angles[mei[0]]
                    
            pos = (centre[0] + ray * sin(ang*pi/180) ,
                   centre[1] - ray * cos(ang*pi/180))
            bmp = constantes.imagesCI[i].GetBitmap()
#                bmp.SetMaskColour(self.backGround)
#                mask = wx.Mask(bmp, self.backGround)
#                bmp.SetMask(mask)
#                bmp.SetMaskColour(wx.NullColour)
#                r = CustomCheckBox(self, 100+i, pos = pos, style = wx.NO_BORDER)
            r = platebtn.PlateButton(self, 100+i, "", bmp, pos = pos, 
                                     style=platebtn.PB_STYLE_GRADIENT|platebtn.PB_STYLE_TOGGLE|platebtn.PB_STYLE_NOBG)#platebtn.PB_STYLE_DEFAULT|
            r.SetPressColor(wx.Colour(245, 55, 245))
            self.bouton.append(r)
#                r = buttons.GenBitmapToggleButton(self, 100+i, bmp, pos = pos, style=wx.BORDER_NONE)
#                r.SetBackgroundColour(wx.NullColour)
#                self.group_ctrls.append((r, 0))
#                self.Bind(wx.EVT_CHECKBOX, self.EvtCheck, r )
        
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnButton)
        bmp = images.Cible.GetBitmap()
        self.SetSize((bmp.GetWidth(), bmp.GetHeight()))
        self.SetMinSize((bmp.GetWidth(), bmp.GetHeight()))
        
    ######################################################################################################
    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.SetBackground(wx.Brush(self.backGround))
        dc.Clear()
        bmp = images.Cible.GetBitmap()
        dc.DrawBitmap(bmp, 0, 0)
        
        evt.Skip()
        
        
    ######################################################################################################
    def OnEraseBackground(self, evt):
        """
        Add a picture to the background
        """
        # yanked from ColourDB.py
        dc = evt.GetDC()
 
        if not dc:
            dc = wx.ClientDC(self)
            rect = self.GetUpdateRegion().GetBox()
            dc.SetClippingRect(rect)
        dc.SetBackgroundMode(wx.TRANSPARENT)
#        color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BACKGROUND)
        dc.SetBackground(wx.Brush(self.backGround))
        dc.Clear()
        bmp = constantes.images.Cible.GetBitmap()
        dc.DrawBitmap(bmp, 0, 0)    
    
    
    #############################################################################            
    def OnButton(self, event):
        button_selected = event.GetEventObject().GetId()-100
        t = u""
        if event.GetEventObject().IsPressed():
            self.CI.AddNum(button_selected)
            t = u"Ajout d'un CI"
        else:
            try: # sinon probléme avec les doubles clics
                self.CI.DelNum(button_selected)
                t = u"Suppression d'un CI"
            except:
                pass

        self.GererBoutons()
        
        self.Layout()
        self.Parent.group_ctrls[button_selected][0].SetValue(event.GetEventObject().IsPressed())
        self.Parent.sendEvent(modif = t)    
        
        
    #############################################################################            
    def GererBoutons(self, appuyer = False):
        """ Permet de cacher les boutons des CI au fur et à mesure que l'on selectionne des CI
            Régles :
             - Maximum 2 CI
             - CI voisins sur la cible
            <appuyer> : pour initialisation : si vrai = appuie sur les boutons
        """
#        print "GererBoutons"
        if len(self.CI.numCI) == 0 or not self.CI.max2CI:
            l = range(len(self.CI.parent.classe.referentiel.CentresInterets))
            
        elif len(self.CI.numCI) == 1:
            l = []
            for i,p in enumerate(self.CI.parent.classe.referentiel.positions_CI):
                p = p[:3].strip()
                c = self.CI.GetPosCible(0)[:3].strip()

                if len(p) == 0 or len(c) == 0: # Cas des CI "en orbite"
                    l.append(i)
                else:       # Autres cas
                    for d in c:
                        if d in p:  
                            l.append(i)
                            break

        else:
            l = self.CI.numCI
            
                
        for i, b in enumerate(self.bouton):
            if i in l:
                b.Show(True)
            else:
                b.Show(False)
                
        if appuyer:
            for i, b in enumerate(self.bouton):
                if i in self.CI.numCI:
                    b._SetState(platebtn.PLATE_PRESSED)
                else:
                    b._SetState(platebtn.PLATE_NORMAL)
                b._pressed = i in self.CI.numCI
                
        self.Parent.GererCases(l, True)    
                    
                    
####################################################################################
#
#   Classe définissant le panel de propriété d'un lien vers une séquence
#
####################################################################################
class PanelPropriete_LienSequence(PanelPropriete):
    def __init__(self, parent, lien):
        PanelPropriete.__init__(self, parent)
        self.lien = lien
        self.sequence = None
        self.classe = None
        self.construire()
        self.parent = parent
        
    #############################################################################            
    def GetDocument(self):
        return self.lien.parent
        
    #############################################################################            
    def construire(self):
        #
        # Sélection du ficier de séquence
        #
        sb0 = wx.StaticBox(self, -1, u"Fichier de la séquence", size = (200,-1))
        sbs0 = wx.StaticBoxSizer(sb0,wx.HORIZONTAL)
        self.texte = wx.TextCtrl(self, -1, self.lien.path, size = (300, -1),
                                 style = wx.TE_PROCESS_ENTER)
        bt2 =wx.BitmapButton(self, 101, wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE))
        bt2.SetToolTipString(u"Sélectionner un fichier")
        self.Bind(wx.EVT_BUTTON, self.OnClick, bt2)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnText, self.texte)
        self.texte.Bind(wx.EVT_KILL_FOCUS, self.OnLoseFocus)
        sbs0.Add(self.texte)#, flag = wx.EXPAND)
        sbs0.Add(bt2)
        
        #
        # Aperéu de la séquence
        #
        sb1 = wx.StaticBox(self, -1, u"Aperéu de la séquence", size = (210,297))
        sbs1 = wx.StaticBoxSizer(sb1,wx.HORIZONTAL)
        sbs1.SetMinSize((210,297))
        self.apercu = wx.StaticBitmap(self, -1, wx.NullBitmap)
        sbs1.Add(self.apercu, 1)
        
        self.sizer.Add(sbs0, (0,0), flag = wx.EXPAND)
        self.sizer.Add(sbs1, (0,1), (2,1))#, flag = wx.EXPAND)
        
        self.sizer.Layout()
        
    #############################################################################            
    def OnClick(self, event):
        mesFormats = u"Séquence (.seq)|*.seq|" \
                       u"Tous les fichiers|*.*'"
                       
        dlg = wx.FileDialog(self, u"Sélectionner un fichier séquence",
                            defaultFile = "",
                            wildcard = mesFormats,
#                           defaultPath = globdef.DOSSIER_EXEMPLES,
                            style = wx.DD_DEFAULT_STYLE
                            #| wx.DD_DIR_MUST_EXIST
                            #| wx.DD_CHANGE_DIR
                            )

        if dlg.ShowModal() == wx.ID_OK:
            self.lien.path = testRel(dlg.GetPath(), 
                                     self.GetDocument().GetPath())
            self.MiseAJour(sendEvt = True)
        dlg.Destroy()
        
        self.SetFocus()
        
        
    #############################################################################            
    def OnText(self, event):
        self.lien.path = event.GetString()
        self.MiseAJour()
        event.Skip()     
                            
    def OnLoseFocus(self, event):  
        self.lien.path = self.texte.GetValue()
        self.MiseAJour()
        event.Skip()   
                   
    #############################################################################            
    def MiseAJour(self, sendEvt = False):
        self.texte.SetValue(self.lien.path)

#        try:
        if os.path.isfile(self.lien.path):
            fichier = open(self.lien.path,'r')
        else:
            abspath = os.path.join(self.GetDocument().GetPath(), self.lien.path)
            if os.path.isfile(abspath):
                fichier = open(abspath,'r')
            else:
                self.texte.SetBackgroundColour("pink")
                self.texte.SetToolTipString(u"Le fichier Séquence est introuvable !")
                return False
        self.texte.SetBackgroundColour("white")
        self.texte.SetToolTipString(u"Lien vers un fichier Séquence")
#        except:
#            dlg = wx.MessageDialog(self, u"Le fichier %s\nn'a pas pu étre trouvé !" %self.lien.path,
#                               u"Erreur d'ouverture du fichier",
#                               wx.OK | wx.ICON_WARNING
#                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
#                               )
#            dlg.ShowModal()
#            dlg.Destroy()
#            self.texte.SetBackgroundColour("pink")
#            self.texte.SetToolTipString(u"Le lien vers le fichier Séquence est rompu !")
#            return False
        
        classe = Classe(self.lien.parent.app.parent)
        self.sequence = Sequence(self.lien.parent.app, classe)
        classe.SetDocument(self.sequence)
        
#        try:
        root = ET.parse(fichier).getroot()
        
        # La séquence
        sequence = root.find("Sequence")
        if sequence == None:
            self.sequence.setBranche(root)
        else:
            self.sequence.setBranche(sequence)
        
            # La classe
            classe = root.find("Classe")
            self.sequence.classe.setBranche(classe)
            self.sequence.SetCodes()
            self.sequence.SetLiens()
            self.sequence.VerifPb()
            
        fichier.close()
        
#        except:
#            self.sequence = None
##            dlg = wx.MessageDialog(self, u"Le fichier %s\nn'a pas pu étre ouvert !" %self.lien.path,
##                               u"Erreur d'ouverture du fichier",
##                               wx.OK | wx.ICON_WARNING
##                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
##                               )
##            dlg.ShowModal()
##            dlg.Destroy()
#            self.texte.SetBackgroundColour("pink")
#            self.texte.SetToolTipString(u"Fichier Séquence corrompu !")

    
        if self.sequence:
            bmp = self.sequence.GetApercu().ConvertToImage().Scale(210, 297).ConvertToBitmap()
            self.apercu.SetBitmap(bmp)
            self.lien.SetLabel()
            self.lien.SetImage(bmp)
            self.lien.SetLien()
            self.lien.SetTitre(self.sequence.intitule)

        self.Layout()
        
        if sendEvt:
            self.sendEvent()
            
        return True
            
####################################################################################
#
#   Classe définissant le panel de propriété de la compétence
#
####################################################################################
class PanelPropriete_Competences(PanelPropriete):
    def __init__(self, parent, competence):
        
        self.competence = competence
        
        PanelPropriete.__init__(self, parent)
        
        self.nb = wx.Notebook(self, -1,  size = (21,21), style= wx.BK_DEFAULT)
        pageComp = wx.Panel(self.nb, -1)
        bg_color = self.Parent.GetBackgroundColour()
        pageComp.SetBackgroundColour(bg_color)
        self.pageComp = pageComp   
        pageCompsizer = wx.BoxSizer(wx.HORIZONTAL)
        
        

        pageComp.SetSizer(pageCompsizer)
            
        ref = self.competence.GetReferentiel()
        
#        self.DestroyChildren()
#        if hasattr(self, 'arbre'):
#            self.sizer.Remove(self.arbre)
        self.arbre = ArbreCompetences(self.pageComp, ref, self)
        pageCompsizer.Add(self.arbre, 1, flag = wx.EXPAND)
#        self.pageComp.sizer.Add(self.arbre, (0,0), flag = wx.EXPAND)
#        if not self.pageComp.sizer.IsColGrowable(0):
#            self.pageComp.sizer.AddGrowableCol(0)
#        if not self.pageComp.sizer.IsRowGrowable(0):
#            self.pageComp.sizer.AddGrowableRow(0)
#        self.pageComp.Layout()
        
        self.nb.AddPage(pageComp, ref.nomCompetences) 
        
        if (len(ref.dicFonctions) > 0):
            #
            # La page "Fonctions"
            #
            pageFct = wx.Panel(self.nb, -1)
            self.pageFct = pageFct
            pageFctsizer = wx.BoxSizer(wx.HORIZONTAL)

            self.arbreFct = ArbreFonctionsPrj(pageFct, ref, self)
            pageFctsizer.Add(self.arbreFct, 1, flag = wx.EXPAND)

            pageFct.SetSizer(pageFctsizer)
            self.nb.AddPage(pageFct, ref.nomFonctions) 

            self.pageFctsizer = pageFctsizer
        
        self.sizer.Add(self.nb, (0,0), flag = wx.EXPAND)
        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableRow(0)
        
        self.Layout()
        
    #############################################################################            
    def GetDocument(self):
        return self.competence.parent
    
#    ######################################################################################  
#    def construire(self):
#        ref = self.competence.GetReferentiel()
#        
#        self.DestroyChildren()
##        if hasattr(self, 'arbre'):
##            self.sizer.Remove(self.arbre)
#        self.arbre = ArbreCompetences(self.pageComp, ref)
#        self.pageComp.sizer.Add(self.arbre, (0,0), flag = wx.EXPAND)
#        if not self.pageComp.sizer.IsColGrowable(0):
#            self.pageComp.sizer.AddGrowableCol(0)
#        if not self.pageComp.sizer.IsRowGrowable(0):
#            self.pageComp.sizer.AddGrowableRow(0)
#        self.pageComp.Layout()
#        
#        self.nb.AddPage(pageComp, ref.nomFonctions) 
#        
#        if (len(ref.dicFonctions) > 0):
#            #
#            # La page "Fonctions"
#            #
#            pageFct = wx.Panel(self.nb, -1)
#            self.pageFct = pageFct
#            pageFctsizer = wx.BoxSizer(wx.HORIZONTAL)
#
#            self.arbreFct = ArbreFonctionsPrj(pageFct, ref, self)
#            pageFctsizer.Add(self.arbreFct, 1, flag = wx.EXPAND)
#
#            pageFct.SetSizer(pageFctsizer)
#            self.nb.AddPage(pageFct, ref.nomFonctions) 
#
#            self.pageFctsizer = pageFctsizer
                
                
        

    ######################################################################################  
    def OnSize(self, event):
        self.win.SetMinSize(self.GetClientSize())
        self.Layout()
        event.Skip()
        
    ######################################################################################  
    def AjouterCompetence(self, code, propag = None):
        self.competence.competences.append(code)
        
    ######################################################################################  
    def EnleverCompetence(self, code, propag = None):
        self.competence.competences.remove(code)
        
    ######################################################################################  
    def SetCompetences(self): 
        self.competence.parent.Verrouiller()
        self.sendEvent(modif = u"Ajout/suppression d'une compétance")
        
    #############################################################################            
    def MiseAJour(self, sendEvt = False):
#        print "MiseAJour compétences"
#        print "  ", self.arbre.items.keys()
#        print "   ", self.competence.competences
        self.arbre.UnselectAll()
        for s in self.competence.competences:
            if s in self.arbre.items.keys():
                self.arbre.CheckItem2(self.arbre.items[s])
                    
                    
        
        
        
#        for s in self.competence.competences:
#            
#            i = self.arbre.get_item_by_label(s, self.arbre.GetRootItem())
#            print s, 
#            print i, i.IsOk()
#            if i.IsOk():
#                self.arbre.CheckItem2(i)
        
        if sendEvt:
            self.sendEvent()
#        titre = wx.StaticText(self, -1, u"Compétence :")
#        
#        # Prévoir un truc pour que la liste des compétences tienne compte de celles déja choisies
#        # idée : utiliser cb.CLear, Clear.Append ou cb.Delete
#        listComp = []
#        l = Competences.items()
#        for c in l:
#            listComp.append(c[0] + " " + c[1])
#        listComp.sort()    
#        
#        cb = wx.ComboBox(self, -1, u"Choisir une compétence",
#                         choices = listComp,
#                         style = wx.CB_DROPDOWN
#                         | wx.TE_PROCESS_ENTER
#                         | wx.CB_READONLY
#                         #| wx.CB_SORT
#                         )
#        self.cb = cb
#        
#        self.sizer.Add(titre, (0,0), flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT|wx.LEFT, border = 2)
#        self.sizer.Add(cb, (0,1), flag = wx.EXPAND)
#        self.sizer.Layout()
#        self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox, cb)
        
#    #############################################################################            
#    def EvtComboBox(self, event):
#        self.competence.SetNum(event.GetSelection())
#        self.sendEvent()
#        
#    #############################################################################            
#    def MiseAJour(self, sendEvt = False):
#        self.cb.SetSelection(self.competence.num)
#        if sendEvt:
#            self.sendEvent()
        


####################################################################################
#
#   Classe définissant le panel de propriété de savoirs
#
####################################################################################
class PanelPropriete_Savoirs(PanelPropriete):
    def __init__(self, parent, savoirs, prerequis):
        
        self.savoirs = savoirs
        self.prerequis = prerequis
        PanelPropriete.__init__(self, parent)
        
        self.nb = wx.Notebook(self, -1,  style= wx.BK_DEFAULT)
        
        # Liste des numéros de pages attribués é
        # 0 : savoirs spécifiques de l'enseignement
        # 1 : savoirs d'un éventuel tronc commun
        # 2 : Math
        # 3 : Phys
        self.lstPages = [0,1,2,3]
        
        
        self.pageSavoir     = self.CreerPage()
        self.pageSavoirSpe  = self.CreerPage()
        self.pageSavoirM    = self.CreerPage()
        self.pageSavoirP    = self.CreerPage()
        
#        # Savoirs
#        pageSavoir = PanelPropriete(nb)
#        pageSavoir.SetBackgroundColour(bg_color)
#        self.pageSavoir = pageSavoir
#        nb.AddPage(pageSavoir, u"")
#        
#        
#        # Savoirs autres
#        ref = self.GetDocument().GetReferentiel()
#        if (prerequis and ref.preSavoirs_Math) or (not prerequis and ref.objSavoirs_Math):
#            # Savoirs Maths
#            pageSavoirM = PanelPropriete(nb)
#            pageSavoirM.SetBackgroundColour(bg_color)
#            self.pageSavoirM = pageSavoirM
#            nb.AddPage(pageSavoirM, self.GetDocument().GetReferentiel().nomSavoirs_Math)
#            self.lstPages[2] = nb.GetPageCount()-1
#            print "page Math" , self.lstPages[2]
#            
#        if (prerequis and ref.preSavoirs_Phys) or (not prerequis and ref.objSavoirs_Phys):
#            # Savoirs Physique
#            pageSavoirP = PanelPropriete(nb)
#            pageSavoirP.SetBackgroundColour(bg_color)
#            self.pageSavoirP = pageSavoirP
#            nb.AddPage(pageSavoirP, self.GetDocument().GetReferentiel().nomSavoirs_Phys)
#            self.lstPages[3] = nb.GetPageCount()-1
#            print "page Phys" , self.lstPages[3]
            
        self.sizer.Add(self.nb, (0,1), (2,1), flag = wx.ALL|wx.ALIGN_RIGHT|wx.EXPAND, border = 1)
        
        self.sizer.AddGrowableRow(0)
        self.sizer.AddGrowableCol(1)
            
        self.MiseAJourTypeEnseignement()

        
    #############################################################################            
    def GetDocument(self):
        return self.savoirs.parent
        
        
    ######################################################################################  
    def CreerPage(self):
        bg_color = self.Parent.GetBackgroundColour()
        page = PanelPropriete(self.nb)
        page.SetBackgroundColour(bg_color)
        self.nb.AddPage(page, u"")
        return page
        
        
    ######################################################################################  
    def construire(self):
#        print "Construire Savoirs"
#        print self.GetDocument().GetReferentiel()
        
        # Savoirs de base (SSI ou ETT par exemple)
        self.pageSavoir.DestroyChildren()
        self.arbre = ArbreSavoirs(self.pageSavoir, "B", self.savoirs, self.prerequis)
        self.pageSavoir.sizer.Add(self.arbre, (0,0), flag = wx.EXPAND)
        if not self.pageSavoir.sizer.IsColGrowable(0):
            self.pageSavoir.sizer.AddGrowableCol(0)
        if not self.pageSavoir.sizer.IsRowGrowable(0):
            self.pageSavoir.sizer.AddGrowableRow(0)
        self.pageSavoir.Layout()
            
        ref = self.GetDocument().GetReferentiel()
        if ref.tr_com != []:
            # Il y a un tronc comun (Spécialité STI2D par exemple)
            self.pageSavoirSpe.DestroyChildren()
            self.arbreSpe = ArbreSavoirs(self.pageSavoirSpe, "S", self.savoirs, self.prerequis)
            self.pageSavoirSpe.sizer.Add(self.arbreSpe, (0,0), flag = wx.EXPAND)
            if not self.pageSavoirSpe.sizer.IsColGrowable(0):
                self.pageSavoirSpe.sizer.AddGrowableCol(0)
            if not self.pageSavoirSpe.sizer.IsRowGrowable(0):
                self.pageSavoirSpe.sizer.AddGrowableRow(0)
            self.pageSavoirSpe.Layout()
            
        if (self.prerequis and ref.preSavoirs_Math) or (not self.prerequis and ref.objSavoirs_Math):
            # Savoirs Math
            self.pageSavoirM.DestroyChildren()
            self.arbreM = ArbreSavoirs(self.pageSavoirM, "M", self.savoirs, self.prerequis)
            self.pageSavoirM.sizer.Add(self.arbreM, (0,0), flag = wx.EXPAND)
            if not self.pageSavoirM.sizer.IsColGrowable(0):
                self.pageSavoirM.sizer.AddGrowableCol(0)
            if not self.pageSavoirM.sizer.IsRowGrowable(0):
                self.pageSavoirM.sizer.AddGrowableRow(0)
            self.pageSavoirM.Layout()
            
        if (self.prerequis and ref.preSavoirs_Phys) or (not self.prerequis and ref.objSavoirs_Phys):
            # Savoirs Physique
            self.pageSavoirP.DestroyChildren()
            self.arbreP = ArbreSavoirs(self.pageSavoirP, "P", self.savoirs, self.prerequis)
            self.pageSavoirP.sizer.Add(self.arbreP, (0,0), flag = wx.EXPAND)
            if not self.pageSavoirP.sizer.IsColGrowable(0):
                self.pageSavoirP.sizer.AddGrowableCol(0)
            if not self.pageSavoirP.sizer.IsRowGrowable(0):
                self.pageSavoirP.sizer.AddGrowableRow(0)
            self.pageSavoirP.Layout()
        self.Layout()
#        print " page Math" , self.lstPages[2]
#        print " page Phys" , self.lstPages[3]
    

    ######################################################################################  
    def SetSavoirs(self): 
        self.savoirs.parent.Verrouiller()
        self.sendEvent(modif = u"Ajout/suppression d'un Savoir")
        
    #############################################################################            
    def MiseAJour(self, sendEvt = False):
        """ Coche tous les savoirs a True de self.savoirs.savoirs 
            dans les différents arbres
        """
#        print "MiseAJour Savoirs"
        self.arbre.UnselectAll()
        for s in self.savoirs.savoirs:
#            print "  ",s
#            typ, cod = s[0], s[1:]
            typ = s[0]
            if typ == "S": # Savoir spécialité STI2D
                i = self.arbreSpe.get_item_by_label(s[1:], self.arbreSpe.GetRootItem())
                if i.IsOk():
                    self.arbreSpe.CheckItem2(i)
            elif typ == "M": # Savoir Math
                i = self.arbreM.get_item_by_label(s[1:], self.arbreM.GetRootItem())
                if i.IsOk():
                    self.arbreM.CheckItem2(i)
            elif typ == "P": # Savoir Physique
                i = self.arbreP.get_item_by_label(s[1:], self.arbreP.GetRootItem())
                if i.IsOk():
                    self.arbreP.CheckItem2(i)
            else:
                i = self.arbre.get_item_by_label(s[1:], self.arbre.GetRootItem())
                if i.IsOk():
                    self.arbre.CheckItem2(i)
        
        if sendEvt:
            self.sendEvent()
            
    #############################################################################            
    def MiseAJourTypeEnseignement(self):
#        print "MiseAJourTypeEnseignement Savoirs"
        ref = self.GetDocument().GetReferentiel()
        
        # Il y a un tronc commun : 0 = TC - 1 = Spé
        if ref.tr_com != []:
            ref_tc = REFERENTIELS[ref.tr_com[0]]
            self.nb.SetPageText(0, ref_tc.nomSavoirs + " " + ref_tc.Code)
            if self.lstPages[1] == None:
                self.lstPages[1] = 1
                self.nb.InsertPage(self.lstPages[1], self.pageSavoirSpe, ref.nomSavoirs + " " + ref.Code)
                for i in range(2,4):
                    if self.lstPages[i] != None:
                        self.lstPages[i] += 1
            else:
                self.nb.SetPageText(self.lstPages[1], ref.nomSavoirs + " " + ref.Code)
        
        # Il n'y a pas de tronc commun : 0 = TC - 1 = rien
        else:
            if ref.surnomSavoirs != u"":
                t = ref.surnomSavoirs
            else:
                t = ref.nomSavoirs + " " + ref.Code
            self.nb.SetPageText(0, t)
            if self.lstPages[1] != None:
                self.nb.RemovePage(self.lstPages[1])
                self.lstPages[1] = None
                for i in range(2,4):
                    if self.lstPages[i] != None:
                        self.lstPages[i] -= 1
        
        # Il y a des maths
        if (self.prerequis and ref.preSavoirs_Math) or (not self.prerequis and ref.objSavoirs_Math):
            if self.lstPages[2] == None:
                if self.lstPages[1] != None:
                    self.lstPages[2] = self.lstPages[1] +1
                else:
                    self.lstPages[2] = self.lstPages[0] +1
                self.nb.InsertPage(self.lstPages[2], self.pageSavoirM, ref.nomSavoirs_Math)
                if self.lstPages[3] != None:
                    self.lstPages[3] += 1
            else:
                self.nb.SetPageText(self.lstPages[2], ref.nomSavoirs_Math)
        else:
            if self.lstPages[2] != None:
                self.nb.RemovePage(self.lstPages[2])
                self.lstPages[2]= None
                if self.lstPages[3] != None:
                    self.lstPages[3] -= 1
                    
        # Il y a de la physique
        if (self.prerequis and ref.preSavoirs_Phys) or (not self.prerequis and ref.objSavoirs_Phys):
            if self.lstPages[3] == None:
                if self.lstPages[2] != None:
                    self.lstPages[3] = self.lstPages[2] +1
                elif self.lstPages[1] != None:
                    self.lstPages[3] = self.lstPages[1] +1
                else:
                    self.lstPages[3] = self.lstPages[0] +1
                self.nb.InsertPage(self.lstPages[3], self.pageSavoirP, ref.nomSavoirs_Phys)
            else:
                self.nb.SetPageText(self.lstPages[3], ref.nomSavoirs_Phys)
        else:
            if self.lstPages[3] != None:
                self.nb.RemovePage(self.lstPages[3])
                self.lstPages[3]= None
        
        self.construire()
            
#############################################################################            
    def MiseAJourTypeEnseignement2(self):
#        print "MiseAJourTypeEnseignement Savoirs"
#        ref = REFERENTIELS[self.savoirs.GetTypeEnseignement()]
        ref = self.GetDocument().GetReferentiel()
        
        if ref.tr_com != []:
            ref_tc = REFERENTIELS[ref.tr_com[0]]
            self.nb.SetPageText(0, ref_tc.nomSavoirs + " " + ref_tc.Code)
            if not hasattr(self, 'pageSavoirSpe') or not isinstance(self.pageSavoirSpe, PanelPropriete):
                bg_color = self.Parent.GetBackgroundColour()
                pageSavoirSpe = PanelPropriete(self.nb)
                pageSavoirSpe.SetBackgroundColour(bg_color)
                self.pageSavoirSpe = pageSavoirSpe
                self.nb.InsertPage(self.lstPages[1], pageSavoirSpe, ref.nomSavoirs + ref.Code)
                for i in range(2,4):
                    self.lstPages[i] += 1
                    
        else:
            self.nb.SetPageText(0, ref.nomSavoirs + " " + ref.Code)
            if hasattr(self, 'pageSavoirSpe') and isinstance(self.pageSavoirSpe, PanelPropriete):
                self.nb.DeletePage(self.lstPages[1])
                for i in range(2,4):
                    self.lstPages[i] -= 1
        
        if (self.prerequis and ref.preSavoirs_Math) or (not self.prerequis and ref.objSavoirs_Math):
            if not hasattr(self, 'pageSavoirM') or not isinstance(self.pageSavoirM, PanelPropriete):
                bg_color = self.Parent.GetBackgroundColour()
                pageSavoirM = PanelPropriete(self.nb)
                pageSavoirM.SetBackgroundColour(bg_color)
                self.pageSavoirM = pageSavoirM
#                self.lstPages[2] = self.lstPages[1]+1
                self.nb.InsertPage(self.lstPages[2], pageSavoirM, ref.nomSavoirs_Math)
                self.lstPages[3] += 1
            else:
                self.nb.SetPageText(self.lstPages[2], ref.nomSavoirs_Math)
        else:
            if hasattr(self, 'pageSavoirM') and isinstance(self.pageSavoirM, PanelPropriete):
                self.nb.DeletePage(self.lstPages[2])
                self.lstPages[3] -= 1
                    
                    
        if (self.prerequis and ref.preSavoirs_Phys) or (not self.prerequis and ref.objSavoirs_Phys):
            if not hasattr(self, 'pageSavoirP') or not isinstance(self.pageSavoirP, PanelPropriete):
                bg_color = self.Parent.GetBackgroundColour()
                pageSavoirP = PanelPropriete(self.nb)
                pageSavoirP.SetBackgroundColour(bg_color)
                self.pageSavoirP = pageSavoirP
#                self.lstPages[3] = self.lstPages[2]+1
                print self.lstPages[3]
                self.nb.InsertPage(self.lstPages[3], pageSavoirP, ref.nomSavoirs_Phys)
            else:
                self.nb.SetPageText(self.lstPages[3], ref.nomSavoirs_Phys)
        else:
            if hasattr(self, 'pageSavoirP') and isinstance(self.pageSavoirP, PanelPropriete):
                self.nb.DeletePage(self.lstPages[3])
            

#        if self.savoirs.GetTypeEnseignement() == "SSI":
#            self.nb.SetPageText(0, u"Capacités SSI")
#        else:
#            self.nb.SetPageText(0, u"Savoirs ETT")
#        
#        if self.savoirs.GetTypeEnseignement() not in ["SSI", "ET"]:
#            if not hasattr(self, 'pageSavoirSpe') or not isinstance(self.pageSavoirSpe, PanelPropriete):
#                bg_color = self.Parent.GetBackgroundColour()
#                pageSavoirSpe = PanelPropriete(self.nb)
#                pageSavoirSpe.SetBackgroundColour(bg_color)
#                self.pageSavoirSpe = pageSavoirSpe
#                self.nb.InsertPage(1, pageSavoirSpe, u"Savoirs " + self.savoirs.GetTypeEnseignement())
#        else:
#            if hasattr(self, 'pageSavoirSpe') and isinstance(self.pageSavoirSpe, PanelPropriete):
#                self.nb.DeletePage(1)
        
        self.construire()  
            
####################################################################################
#
#   Classe définissant le panel de propriété de la séance
#
####################################################################################
class PanelPropriete_Seance(PanelPropriete):
    def __init__(self, parent, seance):
        PanelPropriete.__init__(self, parent)
        self.seance = seance

        #
        # Type de séance
        #
        titre = wx.StaticText(self, -1, u"Type : ")
        cbType = wx.combo.BitmapComboBox(self, -1, u"Choisir un type de séance",
                             choices = [], size = (-1,25),
                             style = wx.CB_DROPDOWN
                             | wx.TE_PROCESS_ENTER
                             | wx.CB_READONLY
                             #| wx.CB_SORT
                             )
        self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox, cbType)
        self.cbType = cbType
        self.sizer.Add(titre, (0,0), flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT|wx.ALL, border = 2)
        self.sizer.Add(cbType, (0,1), flag = wx.EXPAND|wx.ALL, border = 2)
        
        
        #
        # Intitulé de la séance
        #
        box = wx.StaticBox(self, -1, u"Intitulé")
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        textctrl = wx.TextCtrl(self, -1, u"", style=wx.TE_MULTILINE)
        bsizer.Add(textctrl, 1, flag = wx.EXPAND)
        self.textctrl = textctrl
#        self.Bind(wx.EVT_TEXT, self.EvtTextIntitule, textctrl)
        self.textctrl.Bind(wx.EVT_KILL_FOCUS, self.EvtTextIntitule)
        
        cb = wx.CheckBox(self, -1, u"Afficher dans la zone de déroulement")
        cb.SetToolTipString(u"Décocher pour afficher l'intitulé\nen dessous de la zone de déroulement de la séquence")
        cb.SetValue(self.seance.intituleDansDeroul)
        bsizer.Add(cb, flag = wx.EXPAND)
        
        vcTaille = VariableCtrl(self, seance.taille, signeEgal = True, slider = False, sizeh = 40,
                                help = u"Taille des caractères", unite = u"%")
        self.Bind(EVT_VAR_CTRL, self.EvtText, vcTaille)
        bsizer.Add(vcTaille, flag = wx.EXPAND)
        self.vcTaille = vcTaille
        
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, cb)
        self.cbInt = cb
        self.sizer.Add(bsizer, (2,0), (2,2), flag = wx.ALIGN_RIGHT|wx.ALL|wx.EXPAND, border = 2)    
        
        
        #
        # Organisation
        #
        box2 = wx.StaticBox(self, -1, u"Organisation")
        bsizer2 = wx.StaticBoxSizer(box2, wx.VERTICAL)
        
        # Durée de la séance
        vcDuree = VariableCtrl(self, seance.duree, coef = 0.25, signeEgal = True, slider = False, sizeh = 30,
                               help = u"Durée de la séance en heures", unite = u"h")
#        textctrl = wx.TextCtrl(self, -1, u"1")
        self.Bind(EVT_VAR_CTRL, self.EvtText, vcDuree)
        self.vcDuree = vcDuree
        bsizer2.Add(vcDuree, flag = wx.EXPAND|wx.ALL, border = 2)
        
        # Effectif
        titre = wx.StaticText(self, -1, u"Effectif : ")
        cbEff = wx.ComboBox(self, -1, u"",
                         choices = [],
                         style = wx.CB_DROPDOWN
                         | wx.TE_PROCESS_ENTER
                         | wx.CB_READONLY
                         #| wx.CB_SORT
                         )
        self.Bind(wx.EVT_COMBOBOX, self.EvtComboBoxEff, cbEff)
        self.cbEff = cbEff
        self.titreEff = titre
        
        bsizer2.Add(titre, flag = wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 2)
        bsizer2.Add(cbEff, flag = wx.EXPAND|wx.LEFT, border = 2)
#        self.sizer.AddGrowableRow(3)
#        self.sizer.Add(self.nombre, (3,2))
        
        # Nombre de séances en paralléle
        vcNombre = VariableCtrl(self, seance.nombre, signeEgal = True, slider = False, sizeh = 30,
                                help = u"Nombre de groupes réalisant simultanément la même séance")
        self.Bind(EVT_VAR_CTRL, self.EvtText, vcNombre)
        self.vcNombre = vcNombre
        bsizer2.Add(vcNombre, flag = wx.EXPAND|wx.ALL, border = 2)
#        self.sizer.AddGrowableRow(5)
        
        # Nombre de rotations
        vcNombreRot = VariableCtrl(self, seance.nbrRotations, signeEgal = True, slider = False, sizeh = 30,
                                help = u"Nombre de rotations successives")
        self.Bind(EVT_VAR_CTRL, self.EvtText, vcNombreRot)
        self.vcNombreRot = vcNombreRot
        bsizer2.Add(vcNombreRot, flag = wx.EXPAND|wx.ALL, border = 2)
        
        self.sizer.Add(bsizer2, (0,2), (4,1), flag =wx.ALL|wx.EXPAND, border = 2)
        
        # Nombre de groupes
#        vcNombreGrp = VariableCtrl(self, seance.nbrGroupes, signeEgal = True, slider = False, sizeh = 30,
#                                help = u"Nombre de groupes occupés simultanément")
#        self.Bind(EVT_VAR_CTRL, self.EvtText, vcNombreRot)
#        self.vcNombreGrp = vcNombreGrp
#        bsizer2.Add(vcNombreGrp, flag = wx.EXPAND|wx.ALL, border = 2)
#        
#        self.sizer.Add(bsizer2, (0,2), (4,1), flag =wx.ALL|wx.EXPAND, border = 2)
        
        
        
        #
        # Démarche
        #
        titre = wx.StaticText(self, -1, u"Démarche : ")
        cbDem = wx.ComboBox(self, -1, u"",
                         choices = [],
                         style = wx.CB_DROPDOWN
                         | wx.TE_PROCESS_ENTER
                         | wx.CB_READONLY
                         #| wx.CB_SORT
                         )
        self.Bind(wx.EVT_COMBOBOX, self.EvtComboBoxDem, cbDem)
        self.cbDem = cbDem
        self.titreDem = titre
        
        
        self.sizer.Add(titre, (1,0), flag = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, border = 2)
        self.sizer.Add(cbDem, (1,1), flag = wx.EXPAND|wx.ALL, border = 2)

        
        #
        # Systémes
        #
        self.box = wx.StaticBox(self, -1, u"Systèmes ou matériels nécessaires", size = (200,200))
        self.box.SetMinSize((200,200))
        self.bsizer = wx.StaticBoxSizer(self.box, wx.VERTICAL)
        self.systemeCtrl = []
        self.ConstruireListeSystemes()
        self.sizer.Add(self.bsizer, (0,3), (4, 1), flag = wx.EXPAND|wx.ALL, border = 2)
    

        #
        # Lien
        #
        box = wx.StaticBox(self, -1, u"Lien externe")
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        self.selec = URLSelectorCombo(self, self.seance.lien, self.seance.GetPath())
        bsizer.Add(self.selec, flag = wx.EXPAND)
        self.btnlien = wx.Button(self, -1, u"Ouvrir le lien externe")
#        self.btnlien.SetMaxSize((-1,30))
        self.btnlien.Hide()
        self.Bind(wx.EVT_BUTTON, self.OnClick, self.btnlien)
        bsizer.Add(self.btnlien, 1,  flag = wx.EXPAND)
        self.sizer.Add(bsizer, (3,4), (1, 1), flag = wx.EXPAND|wx.ALL, border = 2)
        
        #
        # Description de la séance
        #
        dbox = wx.StaticBox(self, -1, u"Description")
        dbsizer = wx.StaticBoxSizer(dbox, wx.VERTICAL)
#        bd = wx.Button(self, -1, u"Editer")
        tc = richtext.RichTextPanel(self, self.seance, toolBar = True)
#        tc.SetMaxSize((-1, 150))
#        dbsizer.Add(bd, flag = wx.EXPAND)
        dbsizer.Add(tc, 1, flag = wx.EXPAND)
#        self.Bind(wx.EVT_BUTTON, self.EvtClick, bd)
        self.sizer.Add(dbsizer, (0,4), (3, 1), flag = wx.EXPAND|wx.ALL, border = 2)
        self.rtc = tc
        # Pour indiquer qu'une édition est déja en cours ...
        self.edition = False  
        
        self.sizer.SetEmptyCellSize((0,0))
        
        #
        # Mise en place
        #
        self.sizer.AddGrowableCol(4)
        self.sizer.AddGrowableRow(2)
#        self.sizer.Layout()
#        self.Layout()
    
    
    ######################################################################################  
    def GetReferentiel(self):
        return self.seance.GetReferentiel()
    
    
    ######################################################################################  
    def SetPathSeq(self, pathSeq):
        self.selec.SetPathSeq(pathSeq)
        
        
    ######################################################################################  
    def OnPathModified(self, lien, marquerModifier = True):
        self.seance.OnPathModified()
        self.btnlien.Show(self.seance.lien.path != "")
        self.Layout()
        self.Refresh()
        
    
    ############################################################################            
    def ConstruireListeSystemes(self):
        self.Freeze()
        if self.seance.typeSeance in ["AP", "ED", "P"]:
            for ss in self.systemeCtrl:
                self.bsizer.Detach(ss)
                ss.Destroy()
                
            self.systemeCtrl = []
            for s in self.seance.systemes:
#                print "   ", type(s), "---", s
                v = VariableCtrl(self, s, signeEgal = False, 
                                 slider = False, fct = None, help = "", sizeh = 30)
                self.Bind(EVT_VAR_CTRL, self.EvtVarSysteme, v)
                self.bsizer.Add(v, flag = wx.ALIGN_RIGHT)#|wx.EXPAND) 
                self.systemeCtrl.append(v)
            self.bsizer.Layout()
            
            if len(self.seance.systemes) > 0:
                self.box.Show(True)
            else:
                self.box.Hide()
        else:
            for ss in self.systemeCtrl:
                self.bsizer.Detach(ss)
                ss.Destroy()
            self.systemeCtrl = []
            self.box.Hide()
            
        self.box.SetMinSize((200,200))
        self.Layout()
        self.Thaw()
    
    
    #############################################################################            
    def MiseAJourListeSystemes(self):
        if self.seance.typeSeance in ["AP", "ED", "P"]:
            self.Freeze()
            for i, s in enumerate(self.seance.systemes):
                self.systemeCtrl[i].Renommer(s.n)
            self.bsizer.Layout()
            self.Layout()
            self.Thaw()

    #############################################################################
    def MiseAJourTypeEnseignement(self):
        dem = len(REFERENTIELS[self.seance.GetClasse().typeEnseignement].demarches) > 0
        self.cbDem.Show(dem)
        self.titreDem.Show(dem)
        
    ############################################################################            
    def GetDocument(self):
        return self.seance.GetDocument()
    
#    #############################################################################            
#    def EvtClick(self, event):
#        if not self.edition:
#            self.win = richtext.RichTextFrame(u"Description de la séance "+ self.seance.code, self.seance)
#            self.edition = True
#            self.win.Show(True)
#        else:
#            self.win.SetFocus()
        
        
    #############################################################################            
    def EvtVarSysteme(self, event):
        self.sendEvent(modif = u"Modification du nombre de systèmes nécessaires")
        
    #############################################################################            
    def EvtCheckBox(self, event):
        self.seance.intituleDansDeroul = event.IsChecked()
        self.sendEvent(modif = u"Ajout/Suppression d'un système nécessaire")
    
    #############################################################################            
    def EvtTextIntitule(self, event):
        self.seance.SetIntitule(self.textctrl.GetValue())
        event.Skip()
        if not self.eventAttente:
            wx.CallLater(DELAY, self.sendEvent, modif = u"Modification de l'intitulé de la Séance")
            self.eventAttente = True
            
    
    #############################################################################            
    def EvtText(self, event):
        t = u""
        if event.GetId() == self.vcDuree.GetId():
            self.seance.SetDuree(event.GetVar().v[0])
            t = u"Modification de la durée de la Séance"
        
        elif event.GetId() == self.vcNombre.GetId():
            self.seance.SetNombre(event.GetVar().v[0])
            t = u"Modification du nombre de groupes réalisant simultanément la méme séance"
        
        elif event.GetId() == self.vcNombreRot.GetId():
            self.seance.SetNombreRot(event.GetVar().v[0])
            t = u"Modification du nombre de rotations successives"
            
        elif event.GetId() == self.vcTaille.GetId():
            self.seance.SetTaille(event.GetVar().v[0])
            t = u"Modification de la taille des caractères"
            
        if not self.eventAttente:
            wx.CallLater(DELAY, self.sendEvent, modif = t)
            self.eventAttente = True
            
   
        
    #############################################################################            
    def EvtComboBox(self, event):
        if self.seance.typeSeance in ["R", "S"] and self.GetReferentiel().listeTypeSeance[event.GetSelection()] not in ["R", "S"]:
            dlg = wx.MessageDialog(self, u"Modifier le type de cette séance entrainera la suppression de toutes les sous séances !\n" \
                                         u"Voulez-vous continuer ?",
                                    u"Modification du type de séance",
                                    wx.YES_NO | wx.ICON_EXCLAMATION
                                    #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                                    )
            res = dlg.ShowModal()
            dlg.Destroy() 
            if res == wx.ID_NO:
                return
            else:
                self.seance.SupprimerSousSeances()
        
        deja = self.seance.typeSeance in ["AP", "ED", "P"]
        
        self.seance.SetType(get_key(self.GetReferentiel().seances, self.cbType.GetStringSelection(), 1))
        self.seance.parent.OrdonnerSeances()
        
        if self.seance.typeSeance in ["AP", "ED", "P"]:
            if not deja:
                for sy in self.seance.GetDocument().systemes:
                    self.seance.AjouterSysteme(nom = sy.nom, construire = False)
        else:
            self.seance.systemes = []
            
        if self.cbEff.IsEnabled() and self.cbEff.IsShown():
            self.seance.SetEffectif(self.cbEff.GetStringSelection())

        self.AdapterAuType()
        self.ConstruireListeSystemes()
        self.Layout()
        self.sendEvent(modif = u"Modification du type de Séance")
       
        
        
    #############################################################################            
    def EvtComboBoxEff(self, event):
        self.seance.SetEffectif(event.GetString())  
        self.sendEvent(modif = u"Modification de l'effectif de la Séance")



    #############################################################################            
    def EvtComboBoxDem(self, event):
        self.seance.SetDemarche(event.GetString())  
        self.sendEvent(modif = u"Modification de la démarche de la Séance")
       
       
        
    #############################################################################            
    def OnClick(self, event):
        self.seance.AfficherLien(self.GetDocument().GetPath())
        
        
    #############################################################################            
    def AdapterAuType(self):
        """ Adapte le panel au type de séance
        """
#        print "AdapterAuType", self.seance
        #
        # Type de parent
        #
        ref = self.GetReferentiel()

        listType = self.seance.GetListeTypes()
        listTypeS = [(ref.seances[t][1], constantes.imagesSeance[t].GetBitmap()) for t in listType] 
        
        n = self.cbType.GetSelection()   
        self.cbType.Clear()
        for s in listTypeS:
            self.cbType.Append(s[0], s[1])
        self.cbType.SetSelection(n)
        self.cbType.Layout()
        
        #
        # Durée
        #
        if self.seance.typeSeance in ["R", "S"]:
            self.vcDuree.Activer(False)
        
        #
        # Effectif
        #
        if self.seance.typeSeance == "":
            listEff = []
        else:
            listEff = ref.effectifsSeance[self.seance.typeSeance]
#        print "  ", listEff
        
        self.cbEff.Show(len(listEff) > 0)
        self.titreEff.Show(len(listEff) > 0)
            
            
        self.vcNombreRot.Show(self.seance.typeSeance == "R")
        
        self.cbEff.Clear()
        for s in listEff:
            self.cbEff.Append(strEffectifComplet(self.seance.GetDocument().classe, s, -1))
        self.cbEff.SetSelection(0)
        
        
        # Démarche       
        if self.seance.typeSeance in ref.activites.keys():
            listDem = ref.demarcheSeance[self.seance.typeSeance]
            dem = len(ref.demarches) > 0
            self.cbDem.Show(dem)
            self.titreDem.Show(dem)
        else:
            self.cbDem.Show(False)
            self.titreDem.Show(False)
            listDem = []


        # Nombre
        self.vcNombre.Show(self.seance.typeSeance in ["AP", "ED"])
            
        self.cbDem.Clear()
        for s in listDem:
            self.cbDem.Append(ref.demarches[s][1])
        self.cbDem.SetSelection(0)
        
        
    #############################################################################            
    def MarquerProblemeDuree(self, etat):
        return
#        self.vcDuree.marquerValid(etat)
        
    #############################################################################            
    def MiseAJour(self, sendEvt = False):
#        print "MiseAJour PP séance"
        self.AdapterAuType()
        ref = self.GetReferentiel()
        if self.seance.typeSeance != "" and ref.seances[self.seance.typeSeance][1] in self.cbType.GetStrings():
            self.cbType.SetSelection(self.cbType.GetStrings().index(ref.seances[self.seance.typeSeance][1]))
        self.textctrl.ChangeValue(self.seance.intitule)
        self.vcDuree.mofifierValeursSsEvt()
        
        if self.cbEff.IsShown():#self.cbEff.IsEnabled() and 
            self.cbEff.SetSelection(ref.findEffectif(self.cbEff.GetStrings(), self.seance.effectif))
        
        if self.cbDem.IsShown():#self.cbDem.IsEnabled() and :
#            print ref.demarches[self.seance.demarche][1]
#            print self.cbDem.GetStrings()
#            print self.seance
            self.cbDem.SetSelection(self.cbDem.GetStrings().index(ref.demarches[self.seance.demarche][1]))
            
        if self.seance.typeSeance in ["AP", "ED", "P"]:
            self.vcNombre.mofifierValeursSsEvt()
        elif self.seance.typeSeance == "R":
            self.vcNombreRot.mofifierValeursSsEvt()
        
        self.vcTaille.mofifierValeursSsEvt()
        
        self.cbInt.SetValue(self.seance.intituleDansDeroul)
        if sendEvt:
            self.sendEvent()
        
        self.MiseAJourLien()
        
        self.ConstruireListeSystemes()
        
        
    #############################################################################            
    def MiseAJourLien(self):
        self.selec.SetPath(toSystemEncoding(self.seance.lien.path))
        self.btnlien.Show(self.seance.lien.path != "")
        self.sizer.Layout()
        
        
    
    def MiseAJourDuree(self):
        self.vcDuree.mofifierValeursSsEvt()
    
    
    
    
    
    
    
    
    
####################################################################################
#
#   Classe définissant le panel de propriété de la tache
#
####################################################################################
class PanelPropriete_Tache(PanelPropriete):
    def __init__(self, parent, tache, revue = 0):
        self.tache = tache
        self.revue = revue
        PanelPropriete.__init__(self, parent)
#        print "init pptache", tache
        if not tache.phase in [tache.projet.getCodeLastRevue(), _S]  \
           and not (tache.phase in TOUTES_REVUES_EVAL and tache.GetReferentiel().compImposees['C']):
            #
            # La page "Généralités"
            #
            nb = wx.Notebook(self, -1,  size = (21,21), style= wx.BK_DEFAULT)
            pageGen = PanelPropriete(nb)
            bg_color = self.Parent.GetBackgroundColour()
            pageGen.SetBackgroundColour(bg_color)
            self.pageGen = pageGen
            nb.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        else:
            #
            # Pas de book pour la revue 2 et la soutenance
            #
            pageGen = self
            self.pageGen = pageGen
            
        
        #
        # Phase
        #
        prj = self.tache.GetProjetRef()
#        lstPhases = [p[1] for k, p in ref.phases_prj.items() if not k in ref.listPhasesEval_prj]
        lstPhases = [prj.phases[k][1] for k in prj.listPhases if not k in prj.listPhasesEval]
        
        if tache.phase in TOUTES_REVUES_SOUT:
            titre = wx.StaticText(pageGen, -1, u"Phase : "+prj.phases[tache.phase][1])
            pageGen.sizer.Add(titre, (0,0), (1,1), flag = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.ALL, border = 5)
        else:
            titre = wx.StaticText(pageGen, -1, u"Phase :")
            cbPhas = wx.combo.BitmapComboBox(pageGen, -1, u"Selectionner la phase",
                                 choices = lstPhases,
                                 style = wx.CB_DROPDOWN
                                 | wx.TE_PROCESS_ENTER
                                 | wx.CB_READONLY
                                 #| wx.CB_SORT
                                 )

            for i, k in enumerate(sorted([k for k in prj.phases.keys() if not k in prj.listPhasesEval])):#ref.listPhases_prj):
                cbPhas.SetItemBitmap(i, constantes.imagesTaches[k].GetBitmap())
            pageGen.Bind(wx.EVT_COMBOBOX, self.EvtComboBox, cbPhas)
            self.cbPhas = cbPhas
            pageGen.sizer.Add(titre, (0,0), flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT|wx.LEFT, border = 5)
            pageGen.sizer.Add(cbPhas, (0,1), flag = wx.EXPAND|wx.ALL, border = 2)
        

        
        #
        # Intitulé de la tache
        #
        if not tache.phase in TOUTES_REVUES_EVAL_SOUT:
            box = wx.StaticBox(pageGen, -1, u"Intitulé de la tâche")
            bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
            textctrl = wx.TextCtrl(pageGen, -1, u"", style=wx.TE_MULTILINE)
            textctrl.SetToolTipString(u"Donner l'intitulé de la tâche\n"\
                                      u" = un simple résumé !\n" \
                                      u"les détails doivent figurer dans la zone\n" \
                                      u"\"Description détaillée de la tâche\"")
            bsizer.Add(textctrl,1, flag = wx.EXPAND)
            self.textctrl = textctrl
            self.boxInt = box
            self.textctrl.Bind(wx.EVT_KILL_FOCUS, self.EvtTextIntitule)
            pageGen.sizer.Add(bsizer, (1,0), (1,2), 
                           flag = wx.EXPAND|wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT|wx.LEFT|wx.RIGHT, border = 2)
            
        
        #
        # Durée de la tache
        #
        if not tache.phase in TOUTES_REVUES_EVAL_SOUT:
            vcDuree = VariableCtrl(pageGen, tache.duree, coef = 0.5, signeEgal = True, slider = False,
                                   help = u"Volume horaire de la tâche en heures", sizeh = 60)
            pageGen.Bind(EVT_VAR_CTRL, self.EvtText, vcDuree)
            self.vcDuree = vcDuree
            pageGen.sizer.Add(vcDuree, (2,0), (1, 2), flag = wx.EXPAND|wx.ALL, border = 2)
        
        
        #
        # Eléves impliqués
        #
        if not tache.phase in TOUTES_REVUES_EVAL_SOUT:
            self.box = wx.StaticBox(pageGen, -1, u"Eléves impliqués")
#            self.box.SetMinSize((150,-1))
            self.bsizer = wx.StaticBoxSizer(self.box, wx.VERTICAL)
            self.elevesCtrl = []
            self.ConstruireListeEleves()
            pageGen.sizer.Add(self.bsizer, (0,2), (4, 1), flag = wx.EXPAND)
        
        
        
        
        #
        # Description de la tâche
        #
        dbox = wx.StaticBox(pageGen, -1, u"Description détaillée de la tâche")
        dbsizer = wx.StaticBoxSizer(dbox, wx.VERTICAL)
#        bd = wx.Button(pageGen, -1, u"Editer")
        tc = richtext.RichTextPanel(pageGen, self.tache, toolBar = True)
        tc.SetToolTipString(u"Donner une description détaillée de la tâche :\n" \
                            u" - les conditions nécessaires\n" \
                            u" - ce qui est fourni\n" \
                            u" - les résultats attendus\n" \
                            u" - les différentes étapes\n" \
                            u" - la répartition du travail entre les élèves\n"\
                            u" - ..."
                            )
#        tc.SetMaxSize((-1, 150))
#        tc.SetMinSize((150, 60))
        dbsizer.Add(tc,1, flag = wx.EXPAND)
#        dbsizer.Add(bd, flag = wx.EXPAND)
#        pageGen.Bind(wx.EVT_BUTTON, self.EvtClick, bd)
        if tache.phase in TOUTES_REVUES_EVAL_SOUT:
            pageGen.sizer.Add(dbsizer, (1,0), (3, 2), flag = wx.EXPAND)
            pageGen.sizer.AddGrowableCol(0)
        else:
            pageGen.sizer.Add(dbsizer, (0,3), (4, 1), flag = wx.EXPAND)
            pageGen.sizer.AddGrowableCol(3)
        self.rtc = tc
        # Pour indiquer qu'une édition est déja en cours ...
        self.edition = False  
        pageGen.sizer.AddGrowableRow(1)
        
#        print ">>>", tache.phase, tache.projet.getCodeLastRevue()
        if not tache.phase in [tache.projet.getCodeLastRevue(), _S] \
           and not (tache.phase in TOUTES_REVUES_EVAL and tache.GetReferentiel().compImposees['C']):
            nb.AddPage(pageGen, u"Propriétés générales")

            #
            # La page "Compétences"
            #
            pageCom = wx.Panel(nb, -1)
            
            self.pageCom = pageCom
            pageComsizer = wx.BoxSizer(wx.HORIZONTAL)
            
            self.arbre = ArbreCompetencesPrj(pageCom, tache.GetReferentiel(), self,
                                             revue = self.tache.phase in TOUTES_REVUES_SOUT, 
                                             eleves = self.tache.phase in TOUTES_REVUES_EVAL_SOUT)
            pageComsizer.Add(self.arbre, 1, flag = wx.EXPAND)
        
            pageCom.SetSizer(pageComsizer)
            nb.AddPage(pageCom, tache.GetReferentiel().nomCompetences + u" à mobiliser") 
            
            self.pageComsizer = pageComsizer
            
#            if (len(tache.GetReferentiel().dicFonctions) > 0) and (not tache.phase in TOUTES_REVUES_EVAL_SOUT):
#                #
#                # La page "Fonctions"
#                #
#                pageFct = wx.Panel(nb, -1)
#                self.pageFct = pageFct
#                pageFctsizer = wx.BoxSizer(wx.HORIZONTAL)
#
#                self.arbreFct = ArbreFonctionsPrj(pageFct, tache.GetReferentiel(), self)
#                pageFctsizer.Add(self.arbreFct, 1, flag = wx.EXPAND)
#
#                pageFct.SetSizer(pageFctsizer)
#                nb.AddPage(pageFct, tache.GetReferentiel().nomFonctions) 
#
#                self.pageFctsizer = pageFctsizer
        
        
            self.sizer.Add(nb, (0,0), flag = wx.EXPAND)
            self.sizer.AddGrowableCol(0)
            self.sizer.AddGrowableRow(0)
        
        #
        # Mise en place
        #
        
        
        self.Layout()
        self.FitInside()
#        wx.CallAfter(self.PostSizeEvent)
        self.Show()
#        wx.CallAfter(self.Layout)
        
        
    ####################################################################################
    def OnPageChanged(self, event):
#        sel = self.nb.GetSelection()
#        self.MiseAJourPoids()
        event.Skip()
        
    ####################################################################################
    def MiseAJourPoids(self):
        for c in self.tache.indicateursEleve[0]:
            self.MiseAJourIndicateurs(c)
            
    ####################################################################################
    def OnSelChanged(self, event):
        item = event.GetItem() 
        self.competence = self.arbre.GetItemText(item).split()[0]
        self.MiseAJourIndicateurs(self.competence)
        
    #############################################################################            
    def MiseAJourIndicateurs(self, competence):
#        print "MiseAJourIndicateurs", competence
        self.Freeze()
        if False:#self.tache.GetTypeEnseignement() != "SSI":
            indicateurs = REFERENTIELS[self.tache.GetTypeEnseignement()].dicIndicateurs
            lab = u"Indicateurs"
            
            # On supprime l'ancienne CheckListBox
            if self.liste != None:
                self.ibsizer.Detach(self.liste)
                self.liste.Destroy()
            
            if competence in indicateurs.keys():
                self.liste = wx.CheckListBox(self.pageCom, -1, choices = indicateurs[competence], style = wx.BORDER_NONE)
    
                lst = self.tache.indicateursEleve[0][competence]
                for i, c in enumerate(lst):
                    self.liste.Check(i, c)
                
                self.ibox.SetLabel(lab+u" "+competence)
                self.Bind(wx.EVT_CHECKLISTBOX, self.EvtCheckListBox, self.liste)
                
            else:
                self.liste = wx.StaticText(self.pageCom, -1, u"Selectionner une compétence pour afficher les indicateurs associés.")
                self.ibox.SetLabel(lab)
                
            self.ibsizer.Add(self.liste,1 , flag = wx.EXPAND)
                
            self.arbre.Layout()
            self.ibsizer.Layout()
            self.pageComsizer.Layout()
        
        else:
            if competence in self.tache.indicateursEleve[0].keys():
                self.arbre.MiseAJour(competence, self.tache.indicateursEleve[0][competence])
            else:
                prj = self.tache.GetProjetRef()
                self.arbre.MiseAJour(competence, prj._dicCompetences_simple[competence][1])
#                self.arbre.MiseAJour(competence, REFERENTIELS[self.tache.GetTypeEnseignement()]._dicCompetences_prj_simple[competence][1])
            
            
        self.Thaw()
        
        
#    ######################################################################################  
#    def EvtCheckListBox(self, event):
#        index = event.GetSelection()
#        
#        if self.competence in self.tache.indicateursEleve[0].keys():
#            lst = self.tache.indicateursEleve[0][self.competence]
#        else:
#            prj = self.tache.GetProjetRef()
#            lst = [self.competence in self.tache.competences]*len(prj.dicIndicateurs[self.competence])
##            lst = [self.competence in self.tache.competences]*len(REFERENTIELS[self.tache.GetTypeEnseignement()].dicIndicateurs_prj[self.competence])
#            
#        lst[index] = self.liste.IsChecked(index)
#        
#        if True in lst and not self.competence in self.tache.competences:
#            self.tache.competences.append(self.competence)
#            self.arbre.CheckItem2(self.arbre.FindItem(self.arbre.GetRootItem(), self.competence), True)
#            self.arbre.SelectItem(self.arbre.FindItem(self.arbre.GetRootItem(), self.competence))
#        if not True in lst and self.competence in self.tache.competences:
#            self.tache.competences.remove(self.competence)
##            self.MiseAJour(sendEvt = False)
#            self.arbre.CheckItem2(self.arbre.FindItem(self.arbre.GetRootItem(), self.competence), False)
#            self.arbre.SelectItem(self.arbre.FindItem(self.arbre.GetRootItem(), self.competence))
#            
#        self.Refresh()    
#        self.sendEvent(modif = u"Modification du type de séance")
#        
#        self.liste.Check()
#        self.tache.indicateurs[]
#        label = self.liste.GetString(index)
#        status = 'un'
#        if self.liste.IsChecked(index):
#            status = ''
#        
#        self.lb.SetSelection(index)    # so that (un)checking also selects (moves the highlight)
        

    ######################################################################################  
    def AjouterCompetence(self, code, propag = True):
#        print "AjouterCompetence !!", self, code
        if not code in self.tache.indicateursEleve[0]:
            self.tache.indicateursEleve[0].append(code)
        
        if propag:
            for i in range(len(self.tache.projet.eleves)):
                self.AjouterCompetenceEleve(code, i+1)
        
        self.tache.projet.SetCompetencesRevuesSoutenance()
        
        
    ######################################################################################  
    def EnleverCompetence(self, code, propag = True):
#        print "EnleverCompetence", self, code
        if code in self.tache.indicateursEleve[0]:
            self.tache.indicateursEleve[0].remove(code)
        # on recommence : pour corriger un bug
        if code in self.tache.indicateursEleve[0]:
            self.tache.indicateursEleve[0].remove(code)
        
        if propag:
            for i in range(len(self.tache.projet.eleves)):
                self.EnleverCompetenceEleve(code, i+1)
    
        self.tache.projet.SetCompetencesRevuesSoutenance()
    
    
    ######################################################################################  
    def AjouterCompetenceEleve(self, code, eleve):
#        print "AjouterCompetenceEleve", self, code
        if hasattr(self.tache, 'indicateursEleve'):
            dicIndic = self.tache.projet.eleves[eleve-1].GetDicIndicateursRevue(self.tache.phase)
            comp = code.split("_")[0]
            if comp in dicIndic.keys():
                if comp != code: # Indicateur seul
                    indic = eval(code.split("_")[1])
                    ok = dicIndic[comp][indic-1]
            else:
                ok = False
                
            if ok and not code in self.tache.indicateursEleve[eleve]:
                self.tache.indicateursEleve[eleve].append(code)
#                self.tache.ActualiserDicIndicateurs()
            
        
    ######################################################################################  
    def EnleverCompetenceEleve(self, code, eleve):
#        print "EnleverCompetenceEleve", self, code
        if hasattr(self.tache, 'indicateursEleve'):
            if code in self.tache.indicateursEleve[eleve]:
                self.tache.indicateursEleve[eleve].remove(code)
            # on recommence : pour corriger un bug
            if code in self.tache.indicateursEleve[eleve]:
                self.tache.indicateursEleve[eleve].remove(code)
#            self.tache.ActualiserDicIndicateurs()
    
    ############################################################################            
    def SetCompetences(self):
        self.GetDocument().MiseAJourDureeEleves()
        wx.CallAfter(self.sendEvent, modif = u"Ajout/Suppression d'une compétence à la Tâche")
        self.tache.projet.Verrouiller()
        
    ############################################################################            
    def ConstruireListeEleves(self):
        if hasattr(self, 'elevesCtrl'):
            self.pageGen.Freeze()
            
            for ss in self.elevesCtrl:
                self.bsizer.Detach(ss)
                ss.Destroy()
                
            self.elevesCtrl = []
            for i, e in enumerate(self.GetDocument().eleves):
                v = wx.CheckBox(self.pageGen, 100+i, e.GetNomPrenom())
                v.SetMinSize((200,-1))
                v.SetValue(i in self.tache.eleves)
                self.pageGen.Bind(wx.EVT_CHECKBOX, self.EvtCheckEleve, v)
                self.bsizer.Add(v, flag = wx.ALIGN_LEFT|wx.ALL, border = 3)#|wx.EXPAND) 
                self.elevesCtrl.append(v)
            self.bsizer.Layout()
            
            if len(self.GetDocument().eleves) > 0:
                self.box.Show(True)
            else:
                self.box.Hide()
    
#            self.box.SetMinSize((200,200))
            self.pageGen.Layout()
            self.pageGen.Thaw()
            
        # On reconstruit l'arbre pour ajouter/enlever des cases "élève"
        if hasattr(self, 'arbre') and self.arbre.eleves:
            self.arbre.ConstruireCasesEleve()
        
        
    #############################################################################            
    def MiseAJourListeEleves(self):
        """ Met à jour la liste des élèves
        """
        if not self.tache.phase in TOUTES_REVUES_EVAL_SOUT:
            self.pageGen.Freeze()
            for i, e in enumerate(self.GetDocument().eleves):
                self.elevesCtrl[i].SetLabel(e.GetNomPrenom())
            self.bsizer.Layout()
            self.pageGen.Layout()
            self.pageGen.Thaw()

    #############################################################################            
    def MiseAJourEleves(self):
        """ Met à jour le cochage des élèves concernés par la tâche
        """
        if not self.tache.phase in TOUTES_REVUES_EVAL_SOUT:
            for i in range(len(self.GetDocument().eleves)):
                self.elevesCtrl[i].SetValue(i in self.tache.eleves)

                
                
        
    ############################################################################            
    def GetDocument(self):
        return self.tache.GetDocument()
    
#    #############################################################################            
#    def EvtClick(self, event):
#        if not self.edition:
#            self.win = richtext.RichTextFrame(u"Description de la tâche "+ self.tache.code, self.tache)
#            self.edition = True
#            self.win.Show(True)
#        else:
#            self.win.SetFocus()
        
        
#    #############################################################################            
#    def EvtVarSysteme(self, event):
#        self.sendEvent(modif = u"Modification ")
#        
        
    
        
        
    #############################################################################            
    def EvtCheckEleve(self, event):
        lst = []
        for i in range(len(self.GetDocument().eleves)):
            if self.elevesCtrl[i].IsChecked():
                lst.append(i)
        self.tache.eleves = lst
        self.GetDocument().MiseAJourDureeEleves()
        self.GetDocument().MiseAJourTachesEleves()
        self.sendEvent(modif = u"Changement d'élève concerné par la tâche")    


    #############################################################################            
    def EvtTextIntitule(self, event):
        txt = self.textctrl.GetValue()
        if self.tache.intitule != txt:
            self.tache.SetIntitule(txt)
            if not self.eventAttente:
                wx.CallLater(DELAY, self.sendEvent, modif = u"Modification de l'intitulé de la Tâche")
                self.eventAttente = True
        event.Skip()
        
    #############################################################################            
    def EvtText(self, event):
        t = u""
        if event.GetId() == self.vcDuree.GetId():
            self.tache.SetDuree(event.GetVar().v[0])
            t = u"Modification de la durée de la Tâche"
#        elif event.GetId() == self.vcNombre.GetId():
#            self.tache.SetNombre(event.GetVar().v[0])
#            t = u"Modification de la durée de la Tâche"
        
        if not self.eventAttente:
            wx.CallLater(DELAY, self.sendEvent, modif = t)
            self.eventAttente = True
        
    #############################################################################            
    def EvtComboBox(self, event):
        """ Changement de phase
        """
#        print "EvtComboBox phase", self.tache, self.tache.phase
        ref = self.tache.GetProjetRef()
        newPhase = ref.getClefDic('phases', self.cbPhas.GetStringSelection(), 1)
#        print "   ", newPhase
#        newPhase = get_key(self.GetReferentiel().NOM_PHASE_TACHE[self.tache.GetTypeEnseignement(True)], 
#                                        self.cbPhas.GetStringSelection())
        if self.tache.phase != newPhase:
            if newPhase == "Rev":
                self.tache.SetDuree(0)
            self.tache.SetPhase(newPhase)
            self.arbre.MiseAJourPhase(newPhase)
            self.pageGen.Layout()
            self.sendEvent(modif = u"Changement de phase de la Tâche")
        
    
    #############################################################################            
    def MiseAJourDuree(self):
        """ Mise à jour du champ de texte de la durée
            (conformément à la valeur de la variable associée)
        """
        if hasattr(self, 'vcDuree'):
            self.vcDuree.mofifierValeursSsEvt()

    
    #############################################################################            
    def MiseAJourCases(self):
#        print "MiseAJourCases", self.tache.phase, self.tache.intitule
        if hasattr(self, 'arbre'):
            self.arbre.UnselectAll()
            
            for codeIndic in self.tache.indicateursEleve[0]:
                if codeIndic in self.arbre.items.keys():
                    item = self.arbre.items[codeIndic]
                    cases = self.arbre.GetItemWindow(item, 3)
                    cases.MiseAJour()
                    cases.Actualiser()
                  
            
    #############################################################################            
    def MiseAJour(self, sendEvt = False):
#        print "MiseAJour", self.tache.phase, self.tache.intitule
        if hasattr(self, 'arbre'):
            self.arbre.UnselectAll()
            
            for codeIndic in self.tache.indicateursEleve[0]:
                if codeIndic in self.arbre.items.keys():
                    item = self.arbre.items[codeIndic]
                    self.arbre.CheckItem2(item)

            
        if hasattr(self, 'textctrl'):
            self.textctrl.SetValue(self.tache.intitule)
        
        if hasattr(self, 'cbPhas') and self.tache.phase != '':
            self.cbPhas.SetStringSelection(self.tache.GetProjetRef().phases[self.tache.phase][1])
            
        if sendEvt:
            self.sendEvent()
        
        
    #############################################################################
    def MiseAJourTypeEnseignement(self, ref):
        if self.tache.phase in TOUTES_REVUES_EVAL and self.tache.GetReferentiel().compImposees['C']:
            pass
        else:
            if hasattr(self, 'arbre'):
                self.arbre.MiseAJourTypeEnseignement(ref)
            if hasattr(self, 'arbreFct'):
                self.arbreFct.MiseAJourTypeEnseignement(ref)
        
        
####################################################################################
#
#   Classe définissant le panel de propriété d'un système
#
####################################################################################
class PanelPropriete_Systeme(PanelPropriete):
    def __init__(self, parent, systeme):
#        print "init", parent
        self.systeme = systeme
        self.parent = parent
        
        PanelPropriete.__init__(self, parent)
        
        if isinstance(systeme.parent, Sequence):
            self.cbListSys = wx.ComboBox(self, -1, u"",
                                         choices = [u""],
                                         style = wx.CB_DROPDOWN
                                         | wx.TE_PROCESS_ENTER
                                         | wx.CB_READONLY
                                         #| wx.CB_SORT
                                         )
            self.MiseAJourListeSys()
            self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox, self.cbListSys)
            self.sizer.Add(self.cbListSys, (0,1), flag = wx.ALIGN_CENTER_VERTICAL|wx.TOP|wx.BOTTOM|wx.LEFT|wx.EXPAND, border = 3)
            
        #
        # Nom
        #
        titre = wx.StaticText(self, -1, u"Nom du système :")
        textctrl = wx.TextCtrl(self, -1, u"")
        self.textctrl = textctrl
        
        self.sizer.Add(titre, (0,0), (1,1), flag = wx.ALIGN_TOP|wx.TOP|wx.BOTTOM|wx.LEFT, border = 3)
        self.sizer.Add(textctrl, (1,0), (1,2),  flag = wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP|wx.BOTTOM|wx.RIGHT, border = 3)
        
        #
        # Nombre de systèmes disponibles en paralléle
        #
        vcNombre = VariableCtrl(self, systeme.nbrDispo, signeEgal = True, slider = False, 
                                help = u"Nombre de d'exemplaires de ce système disponibles simultanément.")
        self.Bind(EVT_VAR_CTRL, self.EvtVar, vcNombre)
        self.vcNombre = vcNombre
        self.sizer.Add(vcNombre, (2,0), (1, 2), flag = wx.TOP|wx.BOTTOM, border = 3)
        
        #
        # Image
        #
        box = wx.StaticBox(self, -1, u"Image du système")
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        image = wx.StaticBitmap(self, -1, wx.NullBitmap)
        self.image = image
        self.SetImage()
        bsizer.Add(image, flag = wx.EXPAND)
        
        bt = wx.Button(self, -1, u"Changer l'image")
        bt.SetToolTipString(u"Cliquer ici pour sélectionner un fichier image")
        bsizer.Add(bt, flag = wx.EXPAND)
        self.Bind(wx.EVT_BUTTON, self.OnClick, bt)
        self.sizer.Add(bsizer, (0,2), (3,1), flag =  wx.EXPAND|wx.ALIGN_RIGHT|wx.TOP|wx.LEFT, border = 2)#wx.ALIGN_CENTER_VERTICAL |
        self.btImg = bt
        
        #
        # Lien
        #
        box = wx.StaticBox(self, -1, u"Lien externe")
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        self.selec = URLSelectorCombo(self, self.systeme.lien, self.systeme.GetPath())
        bsizer.Add(self.selec, flag = wx.EXPAND)
        self.btnlien = wx.Button(self, -1, u"Ouvrir le lien externe")
        self.btnlien.Hide()
        self.Bind(wx.EVT_BUTTON, self.OnClick, self.btnlien)
        bsizer.Add(self.btnlien)
        self.sizer.Add(bsizer, (0,3), (3, 1), flag = wx.EXPAND|wx.TOP|wx.LEFT, border = 2)
        
        self.sizer.AddGrowableCol(3)
#        self.sizer.AddGrowableRow(1)
        self.sizer.Layout()
        
        self.Bind(wx.EVT_TEXT, self.EvtText, textctrl)
        
        
    ######################################################################################  
    def SetPathSeq(self, pathSeq):
        self.selec.SetPathSeq(pathSeq)
        
        
    ######################################################################################  
    def OnPathModified(self, lien, marquerModifier = True):
#        print "OnPathModified", self.systeme.lien.path, lien.path
        self.systeme.OnPathModified()
        self.systeme.propagerChangements()
        self.btnlien.Show(self.systeme.lien.path != "")
        self.Layout()
        self.Refresh()


    #############################################################################            
    def GetDocument(self):
        if isinstance(self.systeme.parent, Sequence):
            return self.systeme.parent
        elif isinstance(self.systeme.parent, Classe):
            return self.systeme.parent.GetDocument()
    
    
    #############################################################################            
    def EvtComboBox(self, evt):
        sel = evt.GetSelection()
        if sel > 0:
            s = self.systeme.parent.classe.systemes[sel-1]
            self.systeme.setBranche(s.getBranche())
            self.systeme.lienClasse = s
            self.Verrouiller(False)
        else:
            self.systeme.lienClasse = None
            self.Verrouiller(True)
        
        self.systeme.SetNom(evt.GetString())
        if isinstance(self.systeme.parent, Sequence):
            self.systeme.parent.MiseAJourNomsSystemes()
            if not self.eventAttente:
                wx.CallLater(DELAY, self.sendEvent, modif = u"Modification des systèmes nécessaires")
                self.eventAttente = True


    #############################################################################            
    def OnClick(self, event):
        if event.GetId() == self.btnlien.GetId():
            self.systeme.AfficherLien(self.GetDocument().GetPath())
        else:
            mesFormats = u"Fichier Image|*.bmp;*.png;*.jpg;*.jpeg;*.gif;*.pcx;*.pnm;*.tif;*.tiff;*.tga;*.iff;*.xpm;*.ico;*.ico;*.cur;*.ani|" \
                           u"Tous les fichiers|*.*'"
            
            dlg = wx.FileDialog(
                                self, message=u"Ouvrir une image",
    #                            defaultDir = self.DossierSauvegarde, 
                                defaultFile = "",
                                wildcard = mesFormats,
                                style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
                                )
                
            # Show the dialog and retrieve the user response. If it is the OK response, 
            # process the data.
            if dlg.ShowModal() == wx.ID_OK:
                # This returns a Python list of files that were selected.
                paths = dlg.GetPaths()
                nomFichier = paths[0]
                self.systeme.image = wx.Image(nomFichier).ConvertToBitmap()
                self.SetImage()
            
            
            
            dlg.Destroy()
        
    #############################################################################            
    def SetImage(self):
#        print "SetImage", self.systeme
        if self.systeme.image != None:
            w, h = self.systeme.image.GetSize()
            wf, hf = 200.0, 100.0
            r = max(w/wf, h/hf)
            _w, _h = w/r, h/r
            self.systeme.image = self.systeme.image.ConvertToImage().Scale(_w, _h).ConvertToBitmap()
            self.image.SetBitmap(self.systeme.image)
        else:
#            print "NullBitmap"
            self.image.SetBitmap(wx.NullBitmap)
            
        self.systeme.SetImage()
        self.Layout()
        
        
    #############################################################################            
    def EvtText(self, event):
        self.systeme.SetNom(event.GetString())
        
        if isinstance(self.systeme.parent, Sequence):
            self.systeme.parent.MiseAJourNomsSystemes()
            if not self.eventAttente:
                wx.CallLater(DELAY, self.sendEvent, modif = u"Modification du nom du Système")
                self.eventAttente = True
        elif isinstance(self.systeme.parent, Classe):
#            print "  ***", self.systeme.parent
            self.systeme.parent.panelPropriete.MiseAJourListeSys(self.systeme.nom)


    #############################################################################            
    def EvtVar(self, event):
        self.systeme.SetNombre()
        
        if isinstance(self.systeme.parent, Sequence):
            if not self.eventAttente:
                wx.CallLater(DELAY, self.sendEvent, modif = u"Modification du nombre de Systèmes disponibles")
                self.eventAttente = True


    #############################################################################            
    def Verrouiller(self, nom = u""):
        """ Vérrouiller les propriétés du Système
            (quand le Système est défini dans la Classe)
            False = vérrouillé
        """
        try:
            self.cbListSys.SetSelection(self.cbListSys.FindString(nom))
        except:
            nom = u""
        etat = nom != u""
        self.textctrl.Show(etat)
        self.vcNombre.Enable(etat)
        self.selec.Enable(etat)
        self.btImg.Enable(etat)
        self.sizer.Layout()
    
    
    #############################################################################            
    def SetSysteme(self, s):
        self.systeme = s
        self.vcNombre.SetVariable(s.nbrDispo)
        self.selec.lien = s.lien
        self.MiseAJour()
    
    
    #############################################################################            
    def MiseAJour(self, sendEvt = False):
        """
        """
#        print "MiseAJour", self.systeme
            
        self.textctrl.ChangeValue(self.systeme.nom)
        self.vcNombre.mofifierValeursSsEvt()
        
        self.SetImage()
        
        if isinstance(self.systeme.parent, Sequence):
            if sendEvt:
                self.sendEvent()
        
        self.MiseAJourLien()
        
        
    #############################################################################            
    def MiseAJourLien(self):
        self.selec.SetPath(toSystemEncoding(self.systeme.lien.path))
        self.btnlien.Show(len(self.systeme.lien.path) > 0)
        self.Layout()


    #############################################################################            
    def MiseAJourListeSys(self, nom = None):
        self.cbListSys.Set([u""]+[s.nom for s in self.systeme.parent.classe.systemes])
        if nom != None:
            self.cbListSys.SetSelection(self.cbListSys.FindString(nom))




####################################################################################
#
#   Classe définissant le panel de propriété d'une personne
#
####################################################################################
class PanelPropriete_Personne(PanelPropriete):
    def __init__(self, parent, personne):
#        print "PanelPropriete_Personne", personne
        self.personne = personne
        self.parent = parent
        
        PanelPropriete.__init__(self, parent)
        
        #
        # Nom
        #
        box = wx.StaticBox(self, -1, u"Identité")
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        titre = wx.StaticText(self, -1, u"Nom :")
        textctrl = wx.TextCtrl(self, 1, u"")
        self.textctrln = textctrl
        
        nsizer = wx.BoxSizer(wx.HORIZONTAL)
        nsizer.Add(titre, flag = wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.TOP|wx.BOTTOM|wx.LEFT, border = 3)
        nsizer.Add(textctrl, flag = wx.ALIGN_RIGHT|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP|wx.BOTTOM|wx.RIGHT, border = 3)
        self.Bind(wx.EVT_TEXT, self.EvtText, textctrl)
        
        #
        # Prénom
        #
        titre = wx.StaticText(self, -1, u"Prénom :")
        textctrl = wx.TextCtrl(self, 2, u"")
        self.textctrlp = textctrl
        
        psizer = wx.BoxSizer(wx.HORIZONTAL)
        psizer.Add(titre, flag = wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.TOP|wx.BOTTOM|wx.LEFT, border = 3)
        psizer.Add(textctrl, flag = wx.ALIGN_RIGHT|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP|wx.BOTTOM|wx.RIGHT, border = 3)
        self.Bind(wx.EVT_TEXT, self.EvtText, textctrl)
        
        bsizer.Add(nsizer, flag = wx.ALIGN_RIGHT|wx.EXPAND)
        bsizer.Add(psizer, flag = wx.ALIGN_RIGHT|wx.EXPAND)
        self.sizer.Add(bsizer, (0,0), flag = wx.EXPAND|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.TOP|wx.BOTTOM|wx.LEFT, border = 2)
        
        
        #
        # Référent
        #
        if hasattr(self.personne, 'referent'):
            box = wx.StaticBox(self, -1, u"Fonction")
            bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
            cb = wx.CheckBox(self, -1, u"Référent")#, style=wx.ALIGN_RIGHT)
            cb.SetValue(self.personne.referent)
            self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, cb)
            self.cbInt = cb
            bsizer.Add(cb, flag = wx.EXPAND|wx.ALL, border = 3)
            self.sizer.Add(bsizer, (0,1), flag = wx.EXPAND|wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT|wx.TOP|wx.BOTTOM|wx.LEFT, border = 2)
        
        
        #
        # Discipline
        #
        if hasattr(self.personne, 'discipline'):
            titre = wx.StaticText(self, -1, u"Discipline :")
            cbPhas = wx.combo.BitmapComboBox(self, -1, constantes.NOM_DISCIPLINES[self.personne.discipline],
                                 choices = constantes.getLstDisciplines(),
                                 style = wx.CB_DROPDOWN
                                 | wx.TE_PROCESS_ENTER
                                 | wx.CB_READONLY
                                 #| wx.CB_SORT
                                 )
#            for i, k in enumerate(constantes.DISCIPLINES):
#                cbPhas.SetItemBitmap(i, constantes.imagesTaches[k].GetBitmap())
            self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox, cbPhas)
            self.cbPhas = cbPhas
            bsizer.Add(titre, flag = wx.EXPAND|wx.TOP|wx.LEFT, border = 3)
            bsizer.Add(cbPhas, flag = wx.EXPAND|wx.BOTTOM|wx.LEFT, border = 3)
#            self.sizer.Add(bsizer, (2,0), flag = wx.EXPAND|wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT|wx.LEFT, border = 2)

        
        
        #|
        # Grilles d'évaluation
        #
        if hasattr(self.personne, 'grille'):
            self.boxGrille = wx.StaticBox(self, -1, u"Grilles d'évaluation")
            self.bsizer = wx.StaticBoxSizer(self.boxGrille, wx.VERTICAL)
            self.sizer.Add(self.bsizer, (1,0), (1,2), flag = wx.EXPAND|wx.TOP|wx.BOTTOM|wx.LEFT, border = 2)
            self.ConstruireSelectGrille()
            
            
        #
        # Avatar
        #
        box = wx.StaticBox(self, -1, u"Portrait")
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        image = wx.StaticBitmap(self, -1, wx.NullBitmap)
        self.image = image
        self.SetImage()
        bsizer.Add(image, flag = wx.EXPAND)
        
        bt = wx.Button(self, -1, u"Changer le portrait")
        bt.SetToolTipString(u"Cliquer ici pour sélectionner un fichier image")
        bsizer.Add(bt, flag = wx.EXPAND|wx.ALIGN_BOTTOM)
        self.Bind(wx.EVT_BUTTON, self.OnClick, bt)
        self.sizer.Add(bsizer, (0,2), (2,1), flag =  wx.EXPAND|wx.ALIGN_RIGHT|wx.TOP|wx.BOTTOM|wx.LEFT, border = 2)#wx.ALIGN_CENTER_VERTICAL |
        
        self.sizer.AddGrowableRow(0)
        self.sizer.AddGrowableCol(1)
        
        self.sizer.Layout()
        
        self.Layout()
        
        
    #############################################################################            
    def ConstruireSelectGrille(self):
#        titres = self.personne.GetReferentiel().nomParties_prj
        if len(self.personne.grille) > 0:
#            lstGrilles = self.personne.grille
#            titres = self.personne.GetReferentiel().nomParties_prj
            
    #            if self.personne.projet.GetTypeEnseignement(simple = True) == "SSI":
    #                lstGrilles = [self.personne.grille[0]]
    #                titres = [u""]
    #            else:
    #                lstGrilles = self.personne.grille
    #                titres = [u"Revues :", u"Soutenance :"]
            
            self.SelectGrille = {}
            for k in self.personne.grille.keys():
                self.SelectGrille[k] = PanelSelectionGrille(self, self.personne, k)
                self.bsizer.Add(self.SelectGrille[k], flag = wx.EXPAND)
            
            self.boxGrille.Show(True)
            
        else:
            self.boxGrille.Show(False)
            
            
            
    #############################################################################            
    def GetDocument(self):
        return self.personne.projet
    
    
    #############################################################################            
    def OnClick(self, event):
#        for k, g in self.personne.grille.items():
#            if event.GetId() == self.btnlien[k].GetId():
#                g.Afficher(self.GetDocument().GetPath())
##        if event.GetId() == self.btnlien[0].GetId():
##            self.personne.grille[0].Afficher(self.GetDocument().GetPath())
##        elif event.GetId() == self.btnlien[1].GetId():
##            self.personne.grille[1].Afficher(self.GetDocument().GetPath())
#            
#        else:
        mesFormats = u"Fichier Image|*.bmp;*.png;*.jpg;*.jpeg;*.gif;*.pcx;*.pnm;*.tif;*.tiff;*.tga;*.iff;*.xpm;*.ico;*.ico;*.cur;*.ani|" \
                       u"Tous les fichiers|*.*'"
        
        dlg = wx.FileDialog(
                            self, message=u"Ouvrir une image",
#                            defaultDir = self.DossierSauvegarde, 
                            defaultFile = "",
                            wildcard = mesFormats,
                            style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
                            )
            
        # Show the dialog and retrieve the user response. If it is the OK response, 
        # process the data.
        if dlg.ShowModal() == wx.ID_OK:
            # This returns a Python list of files that were selected.
            paths = dlg.GetPaths()
            nomFichier = paths[0]
            self.personne.avatar = wx.Image(nomFichier).ConvertToBitmap()
            self.SetImage()
            self.sendEvent(modif = u"Modification du portrait de la personne")
            
        dlg.Destroy()
        
        
    #############################################################################            
    def SetImage(self):
        if self.personne.avatar != None:
            w, h = self.personne.avatar.GetSize()
            wf, hf = 200.0, 100.0
            r = max(w/wf, h/hf)
            _w, _h = w/r, h/r
            self.personne.avatar = self.personne.avatar.ConvertToImage().Scale(_w, _h).ConvertToBitmap()
            self.image.SetBitmap(self.personne.avatar)
        self.personne.SetImage()
        self.Layout()
        
        
        
    #############################################################################            
    def EvtText(self, event):
        if event.GetId() == 1:
            self.personne.SetNom(event.GetString())
        else:
            self.personne.SetPrenom(event.GetString())
        self.personne.projet.MiseAJourNomsEleves()
        if not self.eventAttente:
            wx.CallLater(DELAY, self.sendEvent, modif = u"Modification du nom de la personne")
            self.eventAttente = True
        

    #############################################################################            
    def EvtComboBox(self, event):
        self.personne.SetDiscipline(get_key(constantes.NOM_DISCIPLINES, self.cbPhas.GetStringSelection()))
        self.Layout()
        self.sendEvent(modif = u"Modification de la discipline du professeur")
        
    #############################################################################            
    def EvtCheckBox(self, event):
        self.personne.projet.SetReferent(self.personne, event.IsChecked())
        self.sendEvent(modif = u"Changement de status (référent) du professeur")
        
    #############################################################################            
    def MiseAJourTypeEnseignement(self):
        if hasattr(self.personne, 'grille'):
#            print "MiseAJourTypeEnseignement eleve", self.personne
            if hasattr(self, 'SelectGrille'):
                for sg in self.SelectGrille.values():
                    self.bsizer.Detach(sg)
                    sg.Destroy()
            self.ConstruireSelectGrille()
        
    #############################################################################            
    def MiseAJour(self, sendEvt = False, marquerModifier = True):
        self.textctrln.ChangeValue(self.personne.nom)
        self.textctrlp.ChangeValue(self.personne.prenom)
        if hasattr(self, 'cbPhas'):
            self.cbPhas.SetStringSelection(constantes.NOM_DISCIPLINES[self.personne.discipline])
        if hasattr(self, 'cbInt'):
            self.cbInt.SetValue(self.personne.referent)
        if hasattr(self, 'SelectGrille'):
            for k, select in self.SelectGrille.items():
                select.SetPath(toSystemEncoding(self.personne.grille[k].path), marquerModifier = marquerModifier)
#            self.OnPathModified()
        if sendEvt:
            self.sendEvent()

    ######################################################################################  
    def OnPathModified(self, lien = "", marquerModifier = True):
        if marquerModifier:
            self.personne.projet.GetApp().MarquerFichierCourantModifie()
        self.Layout()
        self.Refresh()
   
        
        
        
class PanelSelectionGrille(wx.Panel):
    def __init__(self, parent, eleve, codeGrille):
        wx.Panel.__init__(self, parent, -1)
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.eleve = eleve
        self.codeGrille = codeGrille
        titre = wx.StaticText(self, -1, eleve.GetProjetRef().parties[codeGrille])
        self.SelectGrille = URLSelectorCombo(self, eleve.grille[codeGrille], 
                                             eleve.projet.GetPath(), 
                                             dossier = False, ext = "Classeur Excel (*.xls*)|*.xls*")
        self.btnlien = wx.Button(self, -1, u"Ouvrir")
        self.btnlien.Show(self.eleve.grille[self.codeGrille].path != "")
        self.Bind(wx.EVT_BUTTON, self.OnClick, self.btnlien)
        sizer.Add(titre, flag = wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 3)
        sizer.Add(self.SelectGrille,1, flag = wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 3)
        sizer.Add(self.btnlien, flag = wx.EXPAND|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 3)
        
        self.Layout()
        self.SetSizerAndFit(sizer)


    #############################################################################            
    def OnClick(self, event):
        self.eleve.grille[self.codeGrille].Afficher(self.eleve.GetDocument().GetPath())
                
                
    #############################################################################            
    def SetPath(self, path, marquerModifier):  
        self.SelectGrille.SetPath(path, marquerModifier = marquerModifier)          
                
                
    ######################################################################################  
    def OnPathModified(self, lien = "", marquerModifier = True):
        self.btnlien.Show(self.eleve.grille[self.codeGrille].path != "")
        self.Parent.OnPathModified(lien, marquerModifier)
                
                
                
####################################################################################
#
#   Classe définissant le panel de propriété d'un support de projet
#
####################################################################################
class PanelPropriete_Support(PanelPropriete):
    def __init__(self, parent, support):
        
        self.support = support
        self.parent = parent
        
        PanelPropriete.__init__(self, parent)
        
        #
        # Nom
        #
        box = wx.StaticBox(self, -1, u"Nom du support :")
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        textctrl = wx.TextCtrl(self, -1, u"")
        self.textctrl = textctrl
        bsizer.Add(textctrl, flag = wx.EXPAND)
        self.sizer.Add(bsizer, (0,0), flag = wx.EXPAND|wx.TOP|wx.BOTTOM|wx.LEFT, border = 3)

        
        #
        # Lien
        #
        box = wx.StaticBox(self, -1, u"Lien externe")
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        self.selec = URLSelectorCombo(self, self.support.lien, self.support.GetPath())
        bsizer.Add(self.selec, flag = wx.EXPAND)
        self.btnlien = wx.Button(self, -1, u"Ouvrir le lien externe")
        self.btnlien.Hide()
        self.Bind(wx.EVT_BUTTON, self.OnClick, self.btnlien)
        bsizer.Add(self.btnlien)
        self.sizer.Add(bsizer, (1,0), flag = wx.EXPAND|wx.LEFT, border = 3)
        
        
        #
        # Image
        #
        box = wx.StaticBox(self, -1, u"Image du support")
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        image = wx.StaticBitmap(self, -1, wx.NullBitmap)
        image.Bind(wx.EVT_RIGHT_UP, self.OnRClickImage)
        self.image = image
        self.SetImage()
        bsizer.Add(image, flag = wx.EXPAND)
        bt = wx.Button(self, -1, u"Changer l'image")
        bt.SetToolTipString(u"Cliquer ici pour sélectionner un fichier image")
        bsizer.Add(bt, flag = wx.EXPAND)
        self.Bind(wx.EVT_BUTTON, self.OnClick, bt)
        self.sizer.Add(bsizer, (0,1), (2,1), flag = wx.EXPAND|wx.TOP|wx.BOTTOM|wx.LEFT, border = 3)#wx.ALIGN_CENTER_VERTICAL |

        
        #
        # Description du support
        #
        dbox = wx.StaticBox(self, -1, u"Description")
        dbsizer = wx.StaticBoxSizer(dbox, wx.VERTICAL)
#        bd = wx.Button(self, -1, u"Editer")
        tc = richtext.RichTextPanel(self, self.support, toolBar = True)
        tc.SetMaxSize((-1, 150))
#        dbsizer.Add(bd, flag = wx.EXPAND)
        dbsizer.Add(tc, 1, flag = wx.EXPAND)
#        self.Bind(wx.EVT_BUTTON, self.EvtClick, bd)
        self.sizer.Add(dbsizer, (0,2), (2, 1), flag = wx.EXPAND|wx.TOP|wx.BOTTOM|wx.LEFT, border = 3)
        self.rtc = tc
        # Pour indiquer qu'une édition est déja en cours ...
        self.edition = False  
        
        self.sizer.AddGrowableRow(1)
        self.sizer.AddGrowableCol(2)
        
        self.sizer.Layout()
        
        self.Bind(wx.EVT_TEXT, self.EvtText, textctrl)
        
        self.clip = wx.Clipboard()
        self.x = wx.BitmapDataObject()
        
        
    ######################################################################################  
    def SetPathSeq(self, pathSeq):
        self.selec.SetPathSeq(pathSeq)
        
        
    ######################################################################################  
    def OnPathModified(self, lien, marquerModifier = True):
        self.support.OnPathModified()
        self.btnlien.Show(self.support.lien.path != "")
        self.Layout()
        self.Refresh()
        
        
    #############################################################################            
    def GetDocument(self):
        return self.support.parent
    
    
    #############################################################################            
    def OnRClickImage(self, event):
        self.clip.Open()
        ok = self.clip.GetData(self.x)
        self.clip.Close()
        if ok:
            self.GetFenetreDoc().AfficherMenuContextuel([[u"Coller l'image", self.collerImage, None
                                              ]
                                            ])
            
            
    #############################################################################            
    def OnClick(self, event):
        if event.GetId() == self.btnlien.GetId():
            self.support.AfficherLien(self.GetDocument().GetPath())
        else:
            mesFormats = u"Fichier Image|*.bmp;*.png;*.jpg;*.jpeg;*.gif;*.pcx;*.pnm;*.tif;*.tiff;*.tga;*.iff;*.xpm;*.ico;*.ico;*.cur;*.ani|" \
                           u"Tous les fichiers|*.*'"
            
            dlg = wx.FileDialog(
                                self, message=u"Ouvrir une image",
    #                            defaultDir = self.DossierSauvegarde, 
                                defaultFile = "",
                                wildcard = mesFormats,
                                style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
                                )
                
            # Show the dialog and retrieve the user response. If it is the OK response, 
            # process the data.
            if dlg.ShowModal() == wx.ID_OK:
                # This returns a Python list of files that were selected.
                paths = dlg.GetPaths()
                nomFichier = paths[0]
                self.support.image = wx.Image(nomFichier).ConvertToBitmap()
                self.SetImage(True)
            
            
            
            dlg.Destroy()


    #############################################################################            
    def SetImage(self, sendEvt = False):
        if self.support.image != None:
            w, h = self.support.image.GetSize()
            wf, hf = 200.0, 100.0
            r = max(w/wf, h/hf)
            _w, _h = w/r, h/r
#            self.support.image = self.support.image.ConvertToImage().Scale(_w, _h).ConvertToBitmap()
            self.image.SetBitmap(self.support.image.ConvertToImage().Scale(_w, _h).ConvertToBitmap())
        self.support.SetImage()
        self.Layout()
        
        if sendEvt:
            self.sendEvent(modif = u"Modification de l'illustration du Support",
                           obj = self)


    #############################################################################            
    def collerImage(self, sendEvt = False):
        self.support.image = self.x.GetBitmap()
        self.SetImage(True)
    

    #############################################################################            
    def EvtText(self, event):
        nt = event.GetString()
        if nt == u"":
            nt = self.support.parent.intitule
            self.textctrl.ChangeValue(nt)
        elif self.support.parent.intitule == self.support.nom:
            self.support.parent.SetText(nt)
            self.support.parent.panelPropriete.textctrl.ChangeValue(nt)
        self.support.SetNom(nt)
#        self.support.parent.MiseAJourNomsSystemes()
        if not self.eventAttente:
            wx.CallLater(DELAY, self.sendEvent, modif = u"Modification de l'intitulé du Support")
            self.eventAttente = True
        
#    #############################################################################            
#    def EvtClick(self, event):
#        if not self.edition:
#            self.win = richtext.RichTextFrame(u"Description du support "+ self.support.nom, self.support)
#            self.edition = True
#            self.win.Show(True)
#        else:
#            self.win.SetFocus()
        
    #############################################################################            
    def MiseAJour(self, sendEvt = False):
        self.textctrl.ChangeValue(self.support.nom)
        if sendEvt:
            self.sendEvent()
        self.MiseAJourLien()
        self.SetImage()
        
        
        
    #############################################################################            
    def MiseAJourLien(self):
        self.selec.SetPath(toSystemEncoding(self.support.lien.path))
        self.btnlien.Show(len(self.support.lien.path) > 0)
        self.Layout()
        
        
        
        
        
        
        
        
        

####################################################################################
#
#   Classe définissant l'arbre de structure de base d'un document
#
####################################################################################*
class ArbreDoc(CT.CustomTreeCtrl):
    def __init__(self, parent, classe, panelProp,
                 pos = wx.DefaultPosition,
                 size = wx.DefaultSize,
                 style = wx.SUNKEN_BORDER|wx.WANTS_CHARS,
                 agwStyle = CT.TR_HAS_BUTTONS|CT.TR_HAS_VARIABLE_ROW_HEIGHT | CT.TR_HIDE_ROOT|CT.TR_TOOLTIP_ON_LONG_ITEMS, 
                 ):

        CT.CustomTreeCtrl.__init__(self, parent, -1, pos, size, style, agwStyle)
        self.SetBackgroundColour(wx.WHITE)
        
        #
        # Le panel contenant les panel de propriétés des éléments de séquence
        #
        self.panelProp = panelProp

        #
        # La classe 
        #
        self.classe = classe
        
        #
        # On instancie un panel de propriétés vide pour les éléments qui n'ont pas de propriétés
        #
        self.panelVide = PanelPropriete(self.panelProp)
        self.panelVide.Hide()
        
        #
        # Construction de l'arbre
        #
        root = self.AddRoot("")
        self.classe.ConstruireArbre(self, root)
        self.root = root
        
        self.itemDrag = None
        
        #
        # Gestion des évenements
        #
        self.Bind(CT.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
        self.Bind(CT.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRightDown)
        self.Bind(CT.EVT_TREE_BEGIN_DRAG, self.OnBeginDrag)
        self.Bind(CT.EVT_TREE_END_DRAG, self.OnEndDrag)
        self.Bind(wx.EVT_MOTION, self.OnMove)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)
#        self.Bind(wx.EVT_CHAR, self.OnChar)
        
        self.ExpandAll()
        
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
        
    ######################################################################################################
    def OnEnter(self, event):
        self.SetFocus()
        event.Skip()
        
    
    ###############################################################################################
    def OnKey(self, evt):
        keycode = evt.GetKeyCode()
        item = self.GetSelection()
        
        if keycode == wx.WXK_DELETE:
            self.doc.SupprimerItem(item)
            
        elif evt.ControlDown() and keycode == 67: # Crtl-C
            self.GetItemPyData(item).CopyToClipBoard()


        elif evt.ControlDown() and keycode == 86: # Crtl-V
            self.doc.CollerElem(item = item)
            
        evt.Skip()


    ####################################################################################
    def OnSelChanged(self, event):
        """ Fonction appelée lorsque la selection a été changée dans l'arbre
        
        """
        self.item = event.GetItem()
        data = self.GetItemPyData(self.item)
        
        if data == None:        # pas d'objet associé à la branche
            panelPropriete = self.panelVide
        else:
            if isinstance(data, wx.Panel): # 
                panelPropriete = data
            else:
                panelPropriete = data.panelPropriete

        if hasattr(panelPropriete, 'MiseAJour'):
            panelPropriete.MiseAJour()
        self.panelProp.AfficherPanel(panelPropriete)
        self.parent.Refresh()
        
        #
        # On centre la fiche sur l'objet
        #
        if hasattr(self.classe.doc.GetApp(), 'fiche') and self.classe.doc.centrer:
            self.classe.doc.GetApp().fiche.CentrerSur(data)
        self.classe.doc.centrer = True
        
        event.Skip()
        
    ####################################################################################
    def OnBeginDrag(self, event):
        self.itemDrag = event.GetItem()
#        print self.GetItemPyData(self.itemDrag).GetNiveau(), 
#        print self.GetItemPyData(self.itemDrag).GetProfondeur()
        if self.item:
            event.Allow()

        
        
        
        

####################################################################################
#
#   Classe définissant l'arbre de structure de la séquence
#
####################################################################################
class ArbreSequence(ArbreDoc):
    def __init__(self, parent, sequence, classe, panelProp):

        ArbreDoc.__init__(self, parent, classe, panelProp)
        
        self.parent = parent
        
        #
        # La séquence 
        #
        self.sequence = sequence
        self.doc = sequence
        
        #
        # Les icones des branches
        #
        self.images = {}
        il = wx.ImageList(20, 20)
        for k, i in constantes.dicimages.items() + constantes.imagesSeance.items():
            self.images[k] = il.Add(i.GetBitmap())
        self.AssignImageList(il)
        
        
        #
        # Construction de l'arbre
        #
        self.sequence.ConstruireArbre(self, self.root)
        
        
        self.panelProp.AfficherPanel(self.sequence.panelPropriete)

#        self.CurseurInsert = wx.CursorFromImage(constantes.images.CurseurInsert.GetImage())
        self.CurseurInsertApres = wx.CursorFromImage(constantes.images.Curseur_InsererApres.GetImage())
        self.CurseurInsertDans = wx.CursorFromImage(constantes.images.Curseur_InsererDans.GetImage())
        

            
        
    ####################################################################################
    def AjouterObjectif(self, event = None):
        self.sequence.AjouterObjectif()
        
        
    ####################################################################################
    def SupprimerObjectif(self, event = None, item = None):
        self.sequence.SupprimerObjectif(item)

            
    ####################################################################################
    def AjouterSeance(self, event = None):
        seance = self.sequence.AjouterSeance()
        self.lstSeances.append(self.AppendItem(self.seances, u"Séance :", data = seance))
        
    ####################################################################################
    def AjouterRotation(self, event = None, item = None):
        seance = self.sequence.AjouterRotation(self.GetItemPyData(item))
        self.SetItemText(item, u"Rotation")
        self.lstSeances.append(self.AppendItem(item, u"Séance :", data = seance))
        
    ####################################################################################
    def AjouterSerie(self, event = None, item = None):
        seance = self.sequence.AjouterRotation(self.GetItemPyData(item))
        self.SetItemText(item, u"Rotation")
        self.lstSeances.append(self.AppendItem(item, u"Séance :", data = seance))
        
    ####################################################################################
    def SupprimerSeance(self, event = None, item = None):
        if self.sequence.SupprimerSeance(self.GetItemPyData(item)):
            self.lstSeances.remove(item)
            self.Delete(item)


    ####################################################################################
    def OnRightDown(self, event):
        item = event.GetItem()
        self.sequence.AfficherMenuContextuel(item)

    
    ####################################################################################
    def OnLeftDClick(self, event):
        pt = event.GetPosition()
        item = self.HitTest(pt)[0]
        if item:
            self.sequence.AfficherLien(item)
        event.Skip()                
        

    ####################################################################################
    def OnCompareItems(self, item1, item2):
        i1 = self.GetItemPyData(item1)
        i2 = self.GetItemPyData(item2)
        return int(i1.ordre - i2.ordre)

    ####################################################################################
    def OnMove(self, event):
        if self.itemDrag != None:
            item = self.HitTest(wx.Point(event.GetX(), event.GetY()))[0]
            if item != None:
                dataTarget = self.GetItemPyData(item)
                if isinstance(dataTarget, PanelPropriete_Racine):
                    dataTarget = self.sequence
                dataSource = self.GetItemPyData(self.itemDrag)
                a = self.getActionDnD(dataSource, dataTarget)
                if a == 0:
                    self.SetCursor(wx.StockCursor(wx.CURSOR_NO_ENTRY))
                elif a == 1:
                    self.SetCursor(self.CurseurInsertDans)
                elif a == 2 or a == 3 or a == 4:
                    self.SetCursor(self.CurseurInsertApres)

                    
#                if not isinstance(dataSource, Seance):
#                    self.SetCursor(wx.StockCursor(wx.CURSOR_NO_ENTRY))
#                else:
#                    # Premiére place !
#                    if not isinstance(dataTarget, Seance):
#                        if dataTarget == self.sequence.panelSeances:
#                            self.SetCursor(self.CurseurInsertApres)
#                        else:
#                            self.SetCursor(wx.StockCursor(wx.CURSOR_NO_ENTRY))
#                            
#                    # Autres séances
#                    else:
#                        if dataTarget != dataSource:# and dataTarget.parent == dataSource.parent:
#                            if dataTarget.parent == dataSource.parent or not dataTarget.typeSeance in ["R","S"]:
#                                self.SetCursor(self.CurseurInsertApres)
#                            else:
#                                self.SetCursor(self.CurseurInsertDans)
#                        else:
#                            self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
                        
        event.Skip()
        
    ####################################################################################
    def getActionDnD(self, dataSource, dataTarget):
        """ Renvoie un code indiquant l'action à réaliser en cas de EnDrag :
                0 : rien
                1 : 
                2 : 
                3 : 
        """
        if isinstance(dataSource, Seance) and dataTarget != dataSource:
            if not hasattr(dataTarget, 'GetNiveau') or dataTarget.GetNiveau() + dataSource.GetProfondeur() > 2:
#                print "0.1"
                return 0


            # Insérer "dans"  (racine ou "R" ou "S")  .panelSeances
            if dataTarget == self.sequence \
               or (isinstance(dataTarget, Seance) and dataTarget.typeSeance in ["R","S"]):
                if not dataSource in dataTarget.seances:    # parents différents
#                    print dataSource.typeSeance, dataTarget.seances[0].GetListeTypes()
                    if dataTarget.GetNiveau() + dataSource.GetProfondeur() > 1:
#                        print "0-2"
                        return 0
                    elif not dataSource.typeSeance in dataTarget.seances[0].GetListeTypes():
#                        print "0-3"
                        return 0
                    else:
#                        print "1"
                        return 1
                else:
#                    print "2"
                    return 2
            
            # Insérer "aprés"
            else:
                if dataTarget.parent != dataSource.parent:  # parents différents
#                    print dataSource.typeSeance, dataTarget.GetListeTypes()
                    if not dataSource.typeSeance in dataTarget.GetListeTypes():
#                        print "0-4"
                        return 0
                    else:
#                        print "3"
                        return 3
                else:
#                    print "4"
                    return 4
            
            




#            if isinstance(dataTarget, Seance):
#                # source et target ont le méme parent (méme niveau dans l'arbre)
#                if dataTarget.parent == dataSource.parent:
#                    if dataTarget.typeSeance in ["R","S"]:# rotation ou parallele
#                        if not dataSource in dataTarget.seances:
#                            return 1
#                    else:
#                        return 2
#                
#                # source et target ont des parents différents
#                elif dataTarget.parent != dataSource.parent:
#                    return 3
#            elif dataTarget == self.sequence.panelSeances:
#                return 4
        
        return 0

    ####################################################################################
    def OnEndDrag(self, event):
        """ Gestion des glisser-déposer
        """
        self.item = event.GetItem() 
        dataTarget = self.GetItemPyData(self.item)
        if isinstance(dataTarget, PanelPropriete_Racine):
            dataTarget = self.sequence
        dataSource = self.GetItemPyData(self.itemDrag)
        t = u"Changement de position de la Séance"
        a = self.getActionDnD(dataSource, dataTarget)
        if a == 1:
            lstS = dataSource.parent.seances
            lstT = dataTarget.seances
            s = lstS.index(dataSource)
            lstT.insert(0, lstS.pop(s))
            dataSource.parent = dataTarget
            
            self.sequence.OrdonnerSeances()
            self.sequence.reconstruireBrancheSeances(dataSource.parent, dataTarget)
            self.panelVide.sendEvent(self.sequence, modif = t) # Solution pour déclencher un "redessiner"
        elif a == 2:
            lst = dataSource.parent.seances
            s = lst.index(dataSource)
            lst.insert(0, lst.pop(s))
               
            self.sequence.OrdonnerSeances() 
            self.SortChildren(self.GetItemParent(self.item))
            self.panelVide.sendEvent(self.sequence, modif = t) # Solution pour déclencher un "redessiner"
        elif a == 3:
            lstT = dataTarget.parent.seances
            lstS = dataSource.parent.seances
            s = lstS.index(dataSource)
            t = lstT.index(dataTarget)
            lstT[t+1:t+1] = [dataSource]
            del lstS[s]
            p = dataSource.parent
            dataSource.parent = dataTarget.parent
            
            self.sequence.OrdonnerSeances()
            self.sequence.reconstruireBrancheSeances(dataTarget.parent, p)
            self.panelVide.sendEvent(self.sequence, modif = t) # Solution pour déclencher un "redessiner"
        elif a == 4:
            lst = dataTarget.parent.seances
            s = lst.index(dataSource)
            t = lst.index(dataTarget)
            
            if t > s:
                lst.insert(t, lst.pop(s))
            else:
                lst.insert(t+1, lst.pop(s))
               
            self.sequence.OrdonnerSeances() 
            self.SortChildren(self.GetItemParent(self.item))
            self.panelVide.sendEvent(self.sequence, modif = t) # Solution pour déclencher un "redessiner"
        
        
#        if isinstance(dataSource, Seance) and dataTarget != dataSource:
#            
#            # Insérer "dans"  (racine ou "R" ou "S")
#            if dataTarget == self.sequence.panelSeances \
#               or (isinstance(dataTarget, Seance) and dataTarget.typeSeance in ["R","S"]):
#                if not dataSource in dataTarget.seances:    # changement de parent
#                    
#                else:
#                    
#            
#            # Insérer "aprés"
#            else:
#                print "Insérer aprés"
#                if dataTarget.parent != dataSource.parent:
#                    
#                else:
#                    print "  méme parent"
                    
            
        self.itemDrag = None
        event.Skip()
        
        
        
#    ####################################################################################
#    def OnEndDrag2(self, event):
#        """ Gestion des glisser-déposer
#        """
#        self.item = event.GetItem() 
#        dataTarget = self.GetItemPyData(self.item)
#        dataSource = self.GetItemPyData(self.itemDrag)
#        if dataTarget == self.sequence.panelSeances: # racine des séances
#            dataTarget = self.sequence.seances[0]
#            self.item = self.GetFirstChild(self.item)[0]
#            root = True
#        else:
#            root = False
#            
#        if isinstance(dataSource, Seance) and isinstance(dataTarget, Seance)  and dataTarget != dataSource:
#            
#            # source et target ont le méme parent (méme niveau dans l'arbre)
#            if dataTarget.parent == dataSource.parent:
#                
#                if dataTarget.typeSeance in ["R","S"]:          # rotation ou parallele
#                    if not dataSource in dataTarget.seances:    # changement de parent
#                        lstS = dataSource.parent.seances
#                        lstT = dataTarget.seances
#                        s = lstS.index(dataSource)
#                        lstT.insert(0, lstS.pop(s))
#                        dataSource.parent = dataTarget
#                        
#                        self.sequence.OrdonnerSeances()
#                        self.sequence.reconstruireBrancheSeances(dataSource.parent, dataTarget)
#                        self.panelVide.sendEvent(self.sequence) # Solution pour déclencher un "redessiner"
#                    
#                else:
#                    lst = dataTarget.parent.seances
#
#                    s = lst.index(dataSource)
#                    if root:
#                        t = -1
#                    else:
#                        t = lst.index(dataTarget)
#                    
#                    if t > s:
#                        lst.insert(t, lst.pop(s))
#                    else:
#                        lst.insert(t+1, lst.pop(s))
#                       
#                    self.sequence.OrdonnerSeances() 
#                    self.SortChildren(self.GetItemParent(self.item))
#                    self.panelVide.sendEvent(self.sequence) # Solution pour déclencher un "redessiner"
#            
#            # source et target ont des parents différents
#            elif dataTarget.parent != dataSource.parent:
#                lstT = dataTarget.parent.seances
#                lstS = dataSource.parent.seances
#
#                s = lstS.index(dataSource)
#                if root:
#                    t = -1
#                else:
#                    t = lstT.index(dataTarget)
#                lstT[t+1:t+1] = [dataSource]
#                del lstS[s]
#                p = dataSource.parent
#                dataSource.parent = dataTarget.parent
#                
#                self.sequence.OrdonnerSeances()
#                self.sequence.reconstruireBrancheSeances(dataTarget.parent, p)
#                self.panelVide.sendEvent(self.sequence) # Solution pour déclencher un "redessiner"
#            else:
#                pass
#            
#        self.itemDrag = None
#        event.Skip()            

    
    ####################################################################################
    def OnToolTip(self, event):

        item = event.GetItem()
        if item:
            event.SetToolTip(wx.ToolTip(self.GetItemText(item)))

        
    
####################################################################################
#
#   Classe définissant l'arbre de structure d'un projet
#
####################################################################################
class ArbreProjet(ArbreDoc):
    def __init__(self, parent, projet, classe, panelProp):

        ArbreDoc.__init__(self, parent, classe, panelProp)
        
        self.parent = parent
        
        #
        # La séquence 
        #
        self.projet = projet
        self.doc = projet
        
        #
        # Les icones des branches
        #
        self.images = {}
        il = wx.ImageList(20, 20)
        for k, i in constantes.imagesProjet.items() + constantes.imagesTaches.items():
            self.images[k] = il.Add(i.GetBitmap())
        self.AssignImageList(il)
        
        #
        # Construction de l'arbre
        #
        self.projet.ConstruireArbre(self, self.root)
        
        self.panelProp.AfficherPanel(self.projet.panelPropriete)

#        self.CurseurInsert = wx.CursorFromImage(constantes.images.CurseurInsert.GetImage())
        self.CurseurInsertApres = wx.CursorFromImage(constantes.images.Curseur_InsererApres.GetImage())
        self.CurseurInsertDans = wx.CursorFromImage(constantes.images.Curseur_InsererDans.GetImage())
                
        
            
    
            
    ####################################################################################
    def AjouterEleve(self, event = None):
        self.projet.AjouterEleve()
        
        
    ####################################################################################
    def SupprimerEleve(self, event = None, item = None):
        self.projet.SupprimerEleve(item)

            
    ####################################################################################
    def AjouterTache(self, event = None):
        obj = self.GetItemPyData(self.GetSelection())
        if not isinstance(obj, Tache):
            obj = None
        self.projet.AjouterTache(tacheAct = obj)
#        self.lstTaches.append(self.AppendItem(self.taches, u"Tâche :", data = tache))
        
    ####################################################################################
    def SupprimerTache(self, event = None, item = None):
        if self.projet.SupprimerTache(self.GetItemPyData(item)):
            self.lstTaches.remove(item)
            self.Delete(item)

    ####################################################################################
    def Ordonner(self, item):
        self.SortChildren(item)

    ####################################################################################
    def OnRightDown(self, event):
        item = event.GetItem()
        self.projet.AfficherMenuContextuel(item)

    
    ####################################################################################
    def OnLeftDClick(self, event):
        pt = event.GetPosition()
        item = self.HitTest(pt)[0]
        if item:
            self.projet.AfficherLien(item)
        event.Skip()                
        

    ####################################################################################
    def OnCompareItems(self, item1, item2):
        i1 = self.GetItemPyData(item1)
        i2 = self.GetItemPyData(item2)
        return int(i1.ordre - i2.ordre)
#        if i1.phase == i2.phase:
#            
#        else:
#            if i1.phase == "":
#                return -1
#            elif i2.phase == "":
#                return 1
#            else:
#                if i1.phase[0] > i2.phase[0]:
#                    return 1
#                else:
#                    return -1
        

    ####################################################################################
    def OnMove(self, event):
        if self.itemDrag != None:
            item = self.HitTest(wx.Point(event.GetX(), event.GetY()))[0]
            if item != None:
                dataTarget = self.GetItemPyData(item)
                dataSource = self.GetItemPyData(self.itemDrag)
                if not isinstance(dataSource, Tache):
                    self.SetCursor(wx.StockCursor(wx.CURSOR_NO_ENTRY))
                else:
                    if not isinstance(dataTarget, Tache) \
                        or (dataTarget.phase != dataSource.phase and dataSource.phase !="Rev"):
                        self.SetCursor(wx.StockCursor(wx.CURSOR_NO_ENTRY))
                    else:
                        if dataTarget != dataSource:# and dataTarget.parent == dataSource.parent:
                            self.SetCursor(self.CurseurInsertApres)
                        else:
                            self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
                        
        event.Skip()
        
        
    ####################################################################################
    def OnEndDrag(self, event):
        self.item = event.GetItem()
        dataTarget = self.GetItemPyData(self.item)
        dataSource = self.GetItemPyData(self.itemDrag)
        if not isinstance(dataSource, Tache):
            pass
        else:
            if not isinstance(dataTarget, Tache):
                pass
            else:
                if dataTarget != dataSource \
                    and (dataTarget.phase == dataSource.phase or dataSource.phase =="Rev"):
                    lst = dataTarget.projet.taches

                    s = lst.index(dataSource)
                    t = lst.index(dataTarget)
                    
                    if t > s:
                        lst.insert(t, lst.pop(s))
                    else:
                        lst.insert(t+1, lst.pop(s))
                    dataTarget.projet.SetOrdresTaches()
                    self.SortChildren(self.GetItemParent(self.item))
                    self.panelVide.sendEvent(self.projet, modif = u"Changement de position de la Tâche") # Solution pour déclencher un "redessiner"
    
                else:
                    pass
        self.itemDrag = None
        event.Skip()            

    
    ####################################################################################
    def OnToolTip(self, event):

        item = event.GetItem()
        if item:
            event.SetToolTip(wx.ToolTip(self.GetItemText(item)))






            



class ArbreSavoirs(CT.CustomTreeCtrl):
    def __init__(self, parent, typ, savoirs, prerequis):

        CT.CustomTreeCtrl.__init__(self, parent, -1, 
                                   agwStyle = wx.TR_DEFAULT_STYLE|wx.TR_MULTIPLE|wx.TR_HIDE_ROOT|CT.TR_AUTO_CHECK_CHILD|CT.TR_AUTO_CHECK_PARENT)
        
        self.parent = parent
        self.savoirs = savoirs
        
        ref = savoirs.GetReferentiel()
        
        self.root = self.AddRoot(u"")
        
#        if typeEns == "SSI":
#            t = u"Capacités "
#        else:
#            t = u"Savoirs "
#        self.root = self.AppendItem(root, t+typeEns)
        self.SetItemBold(self.root, True)
        et = False
        if typ == "B":
            if ref.tr_com != []:
                dic = REFERENTIELS[ref.tr_com[0]].dicSavoirs
                et = True
            else:
                dic = ref.dicSavoirs
        elif typ == "S":
            dic = ref.dicSavoirs
        elif typ == "M":
            if ref.tr_com != []:
                dic = REFERENTIELS[ref.tr_com[0]].dicSavoirs_Math
            else:
                dic = ref.dicSavoirs_Math
        elif typ == "P":
            if ref.tr_com != []:
                dic = REFERENTIELS[ref.tr_com[0]].dicSavoirs_Phys
            else:
                dic = ref.dicSavoirs_Phys
        self.Construire(self.root, dic, et = et)
            
            
#        if typ == "B":
#            if not typeEns in ["SSI", "ET"]:
#                self.Construire(self.root, REFERENTIELS["ET"].dicSavoirs)
#            else:
#                self.Construire(self.root, REFERENTIELS[typeEns].dicSavoirs)
#        elif typ == "S":
#            self.Construire(self.root, REFERENTIELS[typeEns].dicSavoirs)
#        elif typ == "M":
#            self.Construire(self.root, REFERENTIELS[typeEns].dicSavoirs_Math)
#        elif typ == "P":
#            self.Construire(self.root, REFERENTIELS[typeEns].dicSavoirs_Phys)
            
        self.typ = typ
#        if prerequis and typeEns!="ET" and typeEns!="SSI":
#            self.rootET = self.AppendItem(root, u"Savoirs ETT")
#            self.SetItemBold(self.rootET, True)
#            self.SetItemItalic(self.rootET, True)
#            self.Construire(self.rootET, constantes.dicSavoirs['ET'], )
        
        
        self.ExpandAll()
        
        #
        # Les icones des branches
        #
#        dicimages = {"Seq" : images.Icone_sequence,
#                       "Rot" : images.Icone_rotation,
#                       "Cou" : images.Icone_cours,
#                       "Com" : images.Icone_competence,
#                       "Obj" : images.Icone_objectif,
#                       "Ci" : images.Icone_centreinteret,
#                       "Eva" : images.Icone_evaluation,
#                       "Par" : images.Icone_parallele
#                       }
#        self.images = {}
#        il = wx.ImageList(20, 20)
##        for k, i in dicimages.items():
##            self.images[k] = il.Add(i.GetBitmap())
#        self.AssignImageList(il)
        
        
        #
        # Gestion des évenements
        #
#        self.Bind(CT.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
        self.Bind(CT.EVT_TREE_ITEM_CHECKED, self.OnItemCheck)
        
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)


    ######################################################################################################
    def OnEnter(self, event):
#        print "OnEnter PanelPropriete"
        self.SetFocus()
        event.Skip()
        
    ####################################################################################
    def Construire(self, branche, dic, et = False, grosseBranche = True):
        """ Construction d'une branche de "savoirs"
            <et> = prérequis ETT pour spécialité STI2D
        """
        if dic == None:
            return
        clefs = constantes.trier(dic.keys())
        for k in clefs:
            if type(dic[k][1]) == list:
                sep = u"\n " + CHAR_POINT + u" "
                toolTip = CHAR_POINT + u" " + sep.join(dic[k][1])
            else:
                toolTip = None
#            print k+" "+dic[k][0]
            b = self.AppendItem(branche, k+" "+dic[k][0], ct_type=1, data = toolTip)
            
            if et:
                self.SetItemItalic(b, True)
            if grosseBranche:
                self.SetItemBold(b, True)
#                self.SetItem3State(b, True)
            
            if type(dic[k][1]) == dict:
                self.Construire(b, dic[k][1], et, grosseBranche = False)

        
    ####################################################################################
    def OnItemCheck(self, event):
#        print "OnItemCheck"
#        item = event.GetItem()
#        code = self.GetItemText(item).split()[0]

#        if self.IsItalic(item):
#            code = '_'+code
        

        newSavoirs = []
        for s in self.savoirs.savoirs:
            if s[0] != self.typ:
                newSavoirs.append(s)
                
        newSavoirs.extend(self.getListItemChecked(self.root)[0])    
        
        self.savoirs.savoirs = newSavoirs

#        if item.GetValue():
#            self.savoirs.savoirs.append(code)
#        else:
#            if code in self.savoirs.savoirs:
#                self.savoirs.savoirs.remove(code)
#            else:
#                codeparent = code[:-2]
#                    if codeparent in self.savoirs.savoirs:
                        
                        
        self.parent.Parent.Parent.SetSavoirs()
        event.Skip()
        
        
    ####################################################################################
    def getListItemChecked(self, root):
        liste = []
        complet = True
        for i in root.GetChildren():
            cliste, ccomplet = self.getListItemChecked(i)
            if ccomplet:
                if i.IsChecked():
                    liste.append(self.getCode(i))
                else:
                    complet = False
            else:
                liste.extend(cliste)
                complet = False
             
        return liste, complet
    
    
    ####################################################################################
    def OnGetToolTip(self, event):
        toolTip = event.GetItem().GetData()
        if toolTip != None:
            event.SetToolTip(wx.ToolTip(toolTip))

        
    ####################################################################################
    def traverse(self, parent=None):
        if parent is None:
            parent = self.GetRootItem()
        nc = self.GetChildrenCount(parent, True)

        def GetFirstChild(parent, cookie):
            return self.GetFirstChild(parent)
        
        GetChild = GetFirstChild
        cookie = 1
        for i in range(nc):
            child, cookie = GetChild(parent, cookie)
            GetChild = self.GetNextChild
            yield child
            
            
    ####################################################################################
    def getCode(self, item):
        return self.typ+self.GetItemText(item).split()[0]
    
    
    ####################################################################################
    def get_item_by_label(self, search_text, root_item):
        item, cookie = self.GetFirstChild(root_item)
    
        while item != None and item.IsOk():
            text = self.GetItemText(item)
            if text.split()[0] == search_text:
                return item
            if self.ItemHasChildren(item):
                match = self.get_item_by_label(search_text, item)
                if match.IsOk():
                    return match
            item, cookie = self.GetNextChild(root_item, cookie)
    
        return wx.TreeItemId()




####################################################################################
####################################################################################
####################################################################################
    
class ArbreCompetences(HTL.HyperTreeList):
    def __init__(self, parent, ref, pptache = None, agwStyle = CT.TR_HIDE_ROOT|CT.TR_HAS_VARIABLE_ROW_HEIGHT):#|CT.TR_AUTO_CHECK_CHILD):#|HTL.TR_NO_HEADER):
        
        HTL.HyperTreeList.__init__(self, parent, -1, style = wx.WANTS_CHARS, agwStyle = agwStyle)#wx.TR_DEFAULT_STYLE|
        
        self.parent = parent
        if pptache == None:
            self.pptache = parent
        else:
            self.pptache = pptache
        self.ref = ref
        
        self.items = {}
      
        self.AddColumn(ref.nomCompetences)
        self.SetMainColumn(0) # the one with the tree in it...
        self.AddColumn(u"")
        self.SetColumnWidth(1, 0)
        self.AddColumn(u"")
        self.SetColumnWidth(1, 0)
        self.AddColumn(u"Eleves")
        self.SetColumnWidth(3, 0)
        
        self.root = self.AddRoot(ref.nomCompetences)
        self.MiseAJourTypeEnseignement(ref)
        
        self.ExpandAll()
        
#        il = wx.ImageList(20, 20)
#        self.AssignImageList(il)
        
        #
        # Gestion des évenements
        #
#        self.Bind(CT.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
        self.Bind(CT.EVT_TREE_ITEM_CHECKED, self.OnItemCheck)
        self.Bind(wx.EVT_SIZE, self.OnSize2)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
        self.GetMainWindow().Bind(wx.EVT_MOTION, self.ToolTip)

    ######################################################################################################
    def ToolTip(self, event):
        return
        print self.HitTest((event.x, event.y))
        
    ######################################################################################################
    def OnEnter(self, event):
#        print "OnEnter PanelPropriete"
        self.SetFocus()
        event.Skip()
        
    #############################################################################
    def MiseAJourTypeEnseignement(self, ref):
#        print "MiseAJourTypeEnseignement"
        self.ref = ref
        
        for i in self.items.values():
            for wnd in i._wnd:
                if wnd:
                    wnd.Hide()
                    wnd.Destroy()
                    
        self.DeleteChildren(self.root)
        self.items = {}
        self.Construire(self.root, ref = ref)
        self.ExpandAll()
#        self.Layout()
        
    
    #############################################################################
    def MiseAJourPhase(self, phase):
        self.DeleteChildren(self.root)
        self.Construire(self.root)
        self.ExpandAll()
        
    
    ####################################################################################
    def OnSize2(self, evt):
        ww = 0
        for c in range(1, self.GetColumnCount()):
            ww += self.GetColumnWidth(c)
        w = self.GetClientSize()[0]-20-ww
        if w != self.GetColumnWidth(0):
            self.SetColumnWidth(0, w)
            if self.IsShown():
                self.wrap(w)
        evt.Skip()
        
    ####################################################################################
    def wrap(self,w):
        item = self.GetRootItem()
        while 1:
            item = self.GetNext(item)
            if item == None:
                break
             
            # Coefficient pour le texte en gras (plus large)
            # Et position en X du texte
            if item._type == 0:
                W = w*0.93 - 5
            else:
                W = w - 35
                
            text = self.GetItemText(item, 0).replace("\n", "")
            text = wordwrap(text, W, wx.ClientDC(self))

            self.SetItemText(item, text, 0)
        
    ####################################################################################
    def Construire(self, branche, dic = None, ref = None, ct_type = 0):
        if dic == None:
            dic = ref.dicCompetences
        clefs = dic.keys()
        clefs.sort()
        for k in clefs:
            if type(dic[k]) == list and type(dic[k][1]) == dict:
                b = self.AppendItem(branche, k+" "+dic[k][0], ct_type=ct_type, data = k)
                self.Construire(b, dic[k][1], ct_type = 1)
            else:
                b = self.AppendItem(branche, k+" "+dic[k][0], ct_type = 1, data = k)
            self.items[k] = b
            
            if ct_type == 0:
                self.SetItemBold(b, True)
        
    ####################################################################################
    def OnItemCheck(self, event, item = None):
#        print "OnItemCheck"
        if event != None:
            item = event.GetItem()
        
        self.AjouterEnleverCompetencesItem(item)
        
        if event != None:
            event.Skip()
        wx.CallAfter(self.pptache.SetCompetences)
        
    
    ####################################################################################
    def AjouterEnleverCompetencesItem(self, item, propag = True):
#        print "AjouterEnleverCompetencesItem"
        code = self.GetItemPyData(item)#.split()[0]
#        print "AjouterEnleverCompetencesItem", code
        if code != None: # un seul indicateur séléctionné
            self.AjouterEnleverCompetences([item], propag)

        else:       # une compétence compléte séléctionnée
            self.AjouterEnleverCompetences(item.GetChildren(), propag)

    ####################################################################################
    def AjouterEnleverCompetences(self, lstitem, propag = True):
#        print "AjouterEnleverCompetences"
        for item in lstitem:
            code = self.GetItemPyData(item)#.split()[0]
#            print "  ", code, item.GetValue()
            if item.GetValue():
                self.pptache.AjouterCompetence(code, propag)
            else:
                self.pptache.EnleverCompetence(code, propag)
                
                
    ####################################################################################
    def AjouterEnleverCompetencesEleve(self, lstitem, eleve):
#        print "AjouterEnleverCompetencesEleve", self, lstitem, eleve
        for item in lstitem:
            code = self.GetItemPyData(item)
            if self.GetItemWindow(item, 3).EstCocheEleve(eleve):
                self.pptache.AjouterCompetenceEleve(code, eleve)
            else:
                self.pptache.EnleverCompetenceEleve(code, eleve)
    
    
    ####################################################################################
    def traverse(self, parent=None):
        if parent is None:
            parent = self.GetRootItem()
        nc = self.GetChildrenCount(parent, True)

        def GetFirstChild(parent, cookie):
            return self.GetFirstChild(parent)
        
        GetChild = GetFirstChild
        cookie = 1
        for i in range(nc):
            child, cookie = GetChild(parent, cookie)
            GetChild = self.GetNextChild
            yield child
            
            
    ####################################################################################
    def get_item_by_label(self, search_text, root_item):
        item, cookie = self.GetFirstChild(root_item)
    
        while item != None and item.IsOk():
            text = self.GetItemText(item)
            if text.split()[0] == search_text:
                return item
            if self.ItemHasChildren(item):
                match = self.get_item_by_label(search_text, item)
                if match.IsOk():
                    return match
            item, cookie = self.GetNextChild(root_item, cookie)
    
        return wx.TreeItemId()



class ArbreCompetencesPrj(ArbreCompetences):
    """ Arbre des compétences abordées en projet lors d'une tâche <pptache>
        <revue> : vrai si la tâche est une revue
        <eleves> : vrai s'il faut afficher une colonne supplémentaire pour distinguer les compétences pour chaque éleve
    """
    def __init__(self, parent, ref, pptache, revue = False, eleves = False, 
                 agwStyle = CT.TR_HIDE_ROOT|CT.TR_HAS_VARIABLE_ROW_HEIGHT|\
                            CT.TR_ROW_LINES|CT.TR_ALIGN_WINDOWS| \
                            CT.TR_AUTO_CHECK_PARENT|CT.TR_AUTO_TOGGLE_CHILD):
        self.revue = revue#|CT.TR_AUTO_CHECK_CHILD|\
        self.eleves = eleves
 
        ArbreCompetences.__init__(self, parent, ref, pptache,
                                  agwStyle = agwStyle)#|CT.TR_ELLIPSIZE_LONG_ITEMS)#|CT.TR_TOOLTIP_ON_LONG_ITEMS)#
        self.Bind(wx.EVT_SIZE, self.OnSize2)
        self.Bind(CT.EVT_TREE_ITEM_GETTOOLTIP, self.OnToolTip)
        
        self.SetColumnText(0, ref.nomCompetences + u" et " + ref.nomIndicateurs)
        
        tache = self.pptache.tache
        prj = tache.GetProjetRef()
        
        for i, part in enumerate(prj.parties.keys()):
            self.SetColumnText(i+1, u"Poids "+part)
            self.SetColumnWidth(i+1, 60)
        if eleves:
            self.SetColumnWidth(i+2, 0)
            
          
        
#        self.Bind(CT.EVT_TREE_ITEM_GETTOOLTIP, self.OnToolTip)
        
    ####################################################################################
    def ConstruireCasesEleve(self):
        """ 
        """
#        print "ConstruireCasesEleve"
        tache = self.pptache.tache
#        prj = tache.GetProjetRef()
        for codeIndic, item in self.items.items():
            cases = self.GetItemWindow(item, 3)
            if isinstance(cases, ChoixCompetenceEleve):
                item.DeleteWindow(3)
                cases = ChoixCompetenceEleve(self.GetMainWindow(), codeIndic,
                                             tache.projet, tache)
                item.SetWindow(cases, 3)
            
    

    ####################################################################################
    def Construire(self, branche = None, dic = None, ref = None):
#        print "Construire compétences prj", self.pptache.tache
        if ref == None:
            ref = self.ref
        
        if branche == None:
            branche  = self.root
#        print dic
        
        tache = self.pptache.tache
        prj = tache.GetProjetRef()
        if dic == None: # Construction de la racine
            dic = prj._dicCompetences
        
#        print "   ProjetRef", prj
#        print "   dicCompetences", dic
#        print tache
        
        font = wx.Font(10, wx.DEFAULT, wx.FONTSTYLE_ITALIC, wx.NORMAL, False)
        
#        size = None
        if self.eleves:
            tousEleve = [True]*len(tache.projet.eleves)
        
        def const(d, br, debug = False):
            ks = d.keys()
            ks.sort()
            for k in ks:
                if debug: print "****", k
                v = d[k]
                if len(v) > 1 and type(v[1]) == dict:
                    if debug: print "   ", v[0]
                    
                    if len(v) == 2:
                        b = self.AppendItem(br, k+" "+v[0])
                    
                    else:   # Groupe de compétences - avec poids
                        if debug: print "   prem's", v[2]
                        b = self.AppendItem(br, k+" "+v[0])
#                        print " * ",v[2]
                        
                        for i, part in enumerate(prj.parties.keys()):
                            if part in v[2].keys():
                                self.SetItemText(b, pourCent2(0.01*v[2][part]), i+1)
                        
#                        for i, p in enumerate(v[2][1:]):
#                            if p != 0:
#                                self.SetItemText(b, pourCent2(0.01*p), i+1)
                        self.SetItemBold(b, True)
                    self.items[k] = b
                    const(v[1], b, debug = debug)
                        
                else:   # Indicateur
                    
                    cc = [cd+ " " + it for cd, it in zip(k.split(u"\n"), v[0].split(u"\n"))]
#                    c = self.AppendItem(b, u"\n".join(cc), ct_type=1)
              
                    comp = self.AppendItem(br, u"\n ".join(cc))
                    
                    if len(v) == 3: # Groupe de compétences - avec poids
                        if debug: print "   prem's", v[2]
                        for j, part in enumerate(prj.parties.keys()):
                            if part in v[2].keys():
#                        for i, p in enumerate(v[2][1:]):
#                            if p != 0:
                                self.SetItemText(comp, pourCent2(0.01*v[2][part]), j+1)
                        self.SetItemBold(comp, True)
                                
#                    comp = self.AppendItem(br, k+" "+v[0])
                    
                    self.items[k] = comp
                    b = None #
                    tous = True
                    for i, indic in enumerate(v[1]):
                        codeIndic = str(k+'_'+str(i+1))
                        if debug:
#                            print not tache.phase in [_R1, "Rev", tache.projet.getCodeLastRevue()]
                            print codeIndic , indic.revue,
                            if hasattr(tache, 'indicateursMaxiEleve'):
                                print tache.indicateursMaxiEleve[0]
                            print prj.getTypeIndicateur(codeIndic)
                        
                        if tache == None:
                            b = self.AppendItem(comp, indic.intitule, data = codeIndic)
                            for j, part in enumerate(prj.parties.keys()):
                                if part in v[2].keys():
#                            for j, p in enumerate(indic.poids[1:]):
#                                if p != 0:
                                    if j == 0:
                                        self.SetItemTextColour(b, COUL_PARTIE['C'])
                                    else:
                                        self.SetItemTextColour(b, COUL_PARTIE['S'])
                            self.SetItemFont(b, font)
                            
                            
                        if tache != None and ((not tache.phase in [_R1,_R2, _Rev, tache.projet.getCodeLastRevue()]) \
                                              or (codeIndic in tache.indicateursMaxiEleve[0])) \
                                         and (indic.revue == 0 or indic.revue >= tache.GetProchaineRevue()) \
                                         and (prj.getTypeIndicateur(codeIndic) == "S" or tache.phase != 'XXX'):
                            
                            b = self.AppendItem(comp, indic.intitule, ct_type=1, data = codeIndic)
                            if codeIndic in tache.indicateursEleve[0]:
                                self.CheckItem2(b)
                            else:
                                tous = False
                            
                            if indic.getRevue() == tache.phase:
                                self.CheckItem2(b)
                                
                            if debug: print "   indic", indic
                            
                            for j, part in enumerate(prj.parties.keys()):
                                if part in indic.poids.keys():
#                            for j, p in enumerate(indic.poids[1:]):
#                                if p != 0:
                                    self.SetItemText(b, pourCent2(0.01*indic.poids[part]), j+1)
                                    if part in COUL_PARTIE.keys():
                                        self.SetItemTextColour(b, COUL_PARTIE[part])
                                    else:
                                        self.SetItemTextColour(b, COUL_PARTIE[''])
                            self.SetItemFont(b, font)        
                            
                            self.items[codeIndic] = b
                            
                            if self.eleves:
#                                print "   ", tache.projet.eleves,
                                cases = ChoixCompetenceEleve(self.GetMainWindow(), codeIndic, 
                                                                           tache.projet, 
                                                                           tache)

#                                cases.SetSize(cases.GetBestSize())
                                self.SetItemWindow(b, cases, 3)
                                
                                for e in range(len(tache.projet.eleves)):
                                    tousEleve[e] = tousEleve[e] and self.GetItemWindow(b, 3).EstCocheEleve(e+1)
#                                size = self.GetItemWindow(b, 3).GetSize()[0]
#                                print cases.GetSize()
                                b.SetWindowEnabled(True, 3)
#                                self.Collapse(comp)
#                                self.Refresh()
#                                self.Layout()
                    
                    if b == None: # Désactivation si branche vide d'indicateurs
                        self.SetItemType(br,0)
                    else:
                        self.CheckItem2(br, tous)
#                        if self.eleves:
#                            self.SetItemWindow(c, ChoixCompetenceEleve(self, code, self.pptache.tache.projet, self.pptache.tache), 2)
#                            for e in range(len(self.pptache.tache.projet.eleves)):
#                                self.GetItemWindow(c, 2).CocherEleve(e+1, tousEleve[e])
            return
            
        const(dic, branche, debug = False)
            
        if self.eleves:
            self.SetColumnWidth(3, 60)
        if tache == None: # Cas des arbres dans popup
            self.SetColumnWidth(1, 0)
            self.SetColumnWidth(2, 0)
        
        
#        self.ExpandAll()
#        self.CalculatePositions()
        self.Refresh()
            
        return
    

    #############################################################################
    def MiseAJourCaseEleve(self, codeIndic, etat, eleve, propag = True):
#        print "MiseAJourCaseEleve", codeIndic, etat, eleve, propag
        casesEleves = self.GetItemWindow(self.items[codeIndic], 3)
        if casesEleves.EstCocheEleve(eleve) != etat:
            return
        
        estToutCoche = casesEleves.EstToutCoche()
#        print "  estToutCoche =", estToutCoche
        
        comp = codeIndic.split("_")[0]
        
        if comp != codeIndic: # Indicateur seul
            item = self.items[codeIndic]
            itemComp = self.items[comp]
#            print "  itemComp =", itemComp
            if propag:
                tout = True
                for i in itemComp.GetChildren():
                    tout = tout and self.GetItemWindow(i, 3).EstCocheEleve(eleve)
    #            self.GetItemWindow(itemComp, 2).CocherEleve(eleve, tout)
#                print "MiseAJourCaseEleve", comp, eleve
                cases = self.GetItemWindow(self.items[comp], 3)
                if cases != None:
                    cases.CocherEleve(eleve, tout, withEvent = True)
            
#            self.MiseAJourCaseEleve(comp, tout, eleve, forcer = True)
            
            self.AjouterEnleverCompetencesEleve([item], eleve)
            
            self.CheckItem2(item, estToutCoche, torefresh=True)
#            self.Refresh()
#            self.AjouterEnleverCompetencesItem(item, propag = False)
            
        else: #Compétence complete
            if propag:
                itemComp = self.items[comp]
                for i in itemComp.GetChildren():
    #                self.GetItemWindow(i, 2).CocherEleve(eleve, etat)
    #                self.MiseAJourCaseEleve(self.GetItemPyData(i), etat, eleve, forcer = True)
                    cases = self.GetItemWindow(i, 3)
                    cases.CocherEleve(eleve, etat, withEvent = True)
#            self.CheckItem2(itemComp, estToutCoche)
#            self.AjouterEnleverCompetencesEleve(itemComp.GetChildren(), eleve)
#            self.AjouterEnleverCompetencesItem(itemComp, propag = False)
        
        if propag:
            self.pptache.SetCompetences()
#        wx.CallAfter(self.Refresh)
#        if propag:
#            wx.CallAfter(self.pptache.SetCompetences)
        
        
    #############################################################################
    def OnToolTip(self, event):
        item = event.GetItem()
        if item:
            event.SetToolTip(wx.ToolTip(self.GetItemText(item)))
            




class ArbreFonctionsPrj(ArbreCompetences):
    """ Arbre des fonctions abordées en projet lors d'une tâche <pptache>
        <revue> : vrai si la tâche est une revue
        <eleves> : vrai s'il faut afficher une colonne supplémentaire pour distinguer les compétences pour chaque éleve
    """
    def __init__(self, parent, ref, pptache, 
                 agwStyle = CT.TR_HIDE_ROOT|CT.TR_HAS_VARIABLE_ROW_HEIGHT|\
                            CT.TR_ROW_LINES|CT.TR_ALIGN_WINDOWS|CT.TR_AUTO_CHECK_CHILD|\
                            CT.TR_AUTO_CHECK_PARENT|CT.TR_AUTO_TOGGLE_CHILD):

          
        ArbreCompetences.__init__(self, parent, ref, pptache,
                                  agwStyle = agwStyle)#|CT.TR_ELLIPSIZE_LONG_ITEMS)#|CT.TR_TOOLTIP_ON_LONG_ITEMS)#
        self.Bind(wx.EVT_SIZE, self.OnSize2)
        self.Bind(CT.EVT_TREE_ITEM_GETTOOLTIP, self.OnToolTip)
        
        self.SetColumnText(0, ref.nomFonctions + u" et " + ref.nomTaches)
        
      


    ####################################################################################
    def Construire(self, branche = None, dic = None, ref = None):
#        print "Construire fonctions",
        if ref == None:
            ref = self.ref
#        prj = self.pptache.tache.GetProjetRef()
        
        if dic == None: # Construction de la racine
            dic = ref.dicFonctions
        if branche == None:
            branche  = self.root
#        print dic
#        
#        print "   ", self.GetColumnCount()
        for c in range(1, self.GetColumnCount()):
            self.RemoveColumn(1)
#        print "  ", dic
        for i, c in enumerate(sorted(ref.dicCompetences.keys())):
            self.AddColumn(u"")
            self.SetColumnText(i+1, c)
            self.SetColumnAlignment(i+1, wx.ALIGN_CENTER)
            self.SetColumnWidth(i+1, 30)
            
#        tache = self.pptache.tache
            
#        font = wx.Font(10, wx.DEFAULT, wx.FONTSTYLE_ITALIC, wx.NORMAL, False)
#        
#        size = None
        
        def const(d, br, debug = False):
            ks = d.keys()
            ks.sort()
            for k in ks:
                if debug: print "****", k
                v = d[k]
                if len(v) > 1 and type(v[1]) == dict:
                    if debug: print "   ", v[0]
                    b = self.AppendItem(br, k+" "+v[0])
                    self.items[k] = b
                    const(v[1], b, debug = debug)
                        
                else:   # Extremité de branche
                    cc = [cd+ " " + it for cd, it in zip(k.split(u"\n"), v[0].split(u"\n"))]
                    comp = self.AppendItem(br, u"\n ".join(cc), ct_type=1, data = k)
               
                    if debug: print "   prem's 2", v[1]
                    
                    
                    for c, p in enumerate(sorted(ref.dicCompetences.keys())):
                        if p in v[1]:
#                    for i, p in enumerate(v[1]):
#                        if p == self.GetColumnText(i+1):
                            self.SetItemText(comp, "X", c+1)
                                
                    self.items[k] = comp

#                    if b == None: # Désactivation si branche vide d'indicateurs
#                        self.SetItemType(br,0)
#                    else:
#                        self.CheckItem2(br, tous)

            return
            
        const(dic, branche, debug = False)
            
#        if tache == None: # Cas des arbres dans popup
#            self.SetColumnWidth(1, 0)
#            self.SetColumnWidth(2, 0)
#        self.Refresh()
            
        return
    
        
    #############################################################################
    def OnToolTip(self, event):
        item = event.GetItem()
        if item:
            event.SetToolTip(wx.ToolTip(self.GetItemText(item)))
            
    ####################################################################################
    def OnItemCheck(self, event, item = None):
        pass



class ArbreCompetencesPopup(CT.CustomTreeCtrl):
    """ Arbre des compétences abordées en projet lors d'une tâche <pptache>
        <revue> : vrai si la tâche est une revue
        <eleves> : vrai s'il faut afficher une colonne supplémentaire pour distinguer les compétences pour chaque éleve
    """
    def __init__(self, parent):
          
        CT.CustomTreeCtrl.__init__(self, parent, -1,
                                   agwStyle = CT.TR_HAS_VARIABLE_ROW_HEIGHT|CT.TR_HIDE_ROOT|CT.TR_NO_LINES)
#        self.SetQuickBestSize(False)
        self.root = self.AddRoot(u"")

    ####################################################################################
    def Construire(self, dic , dicIndicateurs, prj):
#        print "Construire", dic
#        print dicIndicateurs
        branche  = self.root
        
        debug = False
            
        font = wx.Font(10, wx.DEFAULT, wx.FONTSTYLE_ITALIC, wx.NORMAL, False)
        
        def const(d, br, debug = False):
            ks = d.keys()
            ks.sort()
            for k in ks:
                if debug: print "****", k
                v = d[k]
                if len(v) > 1 and type(v[1]) == dict:
                    if debug: print "   ", v[0]
                    if len(v) == 2:
                        b = self.AppendItem(br, textwrap.fill(k+" "+v[0], 50))
                    else:
                        if debug: print "   prem's", v[2]
                        b = self.AppendItem(br, textwrap.fill(k+" "+v[0], 50))
                        self.SetItemBold(b, True)

                    const(v[1], b, debug = debug)
                        
                else:   # Indicateur
                    cc = [cd+ " " + it for cd, it in zip(k.split(u"\n"), v[0].split(u"\n"))] 
                    comp = self.AppendItem(br, textwrap.fill(u"\n ".join(cc), 50))
                    if k in dicIndicateurs.keys():
                        ajouteIndic(comp, v[1], dicIndicateurs[k])
                    else:
                        ajouteIndic(comp, v[1], None)
            return
        
        def ajouteIndic(branche, listIndic, listIndicUtil):
            for i, indic in enumerate(listIndic):
                b = self.AppendItem(branche, textwrap.fill(indic.intitule, 50))
                for j, part in enumerate(prj.parties.keys()):
                    if part in indic.poids.keys():
#                for j, p in enumerate(indic.poids[1:]):
#                    if p != 0:
#                        print listIndic
#                        print comp, dicIndicateurs[comp]
                        if listIndicUtil == None or not listIndicUtil[i]:
                            self.SetItemTextColour(b, COUL_ABS)
                        else:
                            self.SetItemTextColour(b, COUL_PARTIE[part])
                self.SetItemFont(b, font)
        
        if type(dic) == dict:  
            const(dic, branche, debug = debug)
        else:
            ajouteIndic(branche, dic, dicIndicateurs)
#        self.Update()
        self.Layout()
        self.Parent.Layout()
        self.Refresh()
        
#        self.SetVirtualSize(self.GetWindowBorderSize()+self.GetBestSize())
        self.AdapterSize()
    

#        self.SetMaxSize(self.GetWindowBorderSize()+self.GetVirtualSize())
 
            
        return
    
    
    def AdapterSize(self):
        self.ExpandAll()
#        self.CalculateSize(self.root, wx.ScreenDC())
#        self.PaintItem(self.root, wx.ScreenDC(), 1, 0)
#        print "Size =", self.GetBestSize(), self.GetClientSize(), 
#        print self.GetEffectiveMinSize(), self.GetBoundingRect(self.root), 
#        print self.GetMinClientSize(), self.GetMaxSize(), self.GetMinSize(), 
#        print self.GetVirtualSize(), self.GetBestVirtualSize(),
#        print self.GetWindowBorderSize()+self.GetVirtualSize(), self.GetMaxWidth(respect_expansion_state=False),
#        print self.DoGetVirtualSize()
        ms = self.GetMaxSize2(self.root)
#        print "   **", ms
#        print self.RecurseOnChildren(self.root, 1000, False)
        self.SetMinSize((ms[0]+5, ms[1]+16))


    def GetMaxSize2(self, item, level = 2, maxwidth=0, lastheight = 0):
        dc = wx.ScreenDC()
#        dc.SetFont(self.GetItemFont())
        
        child, cookie = self.GetFirstChild(item)
#        print " level",level
#        print " ",child, cookie
        while child != None and child.IsOk():
            dc.SetFont(self.GetItemFont(child))
#            print "  txt =",self.GetItemText(child)
            W, H, lH = dc.GetMultiLineTextExtent(self.GetItemText(child))
#            print "  W,H, lH =",W,H, lH, self.GetIndent()
            width = W + self.GetIndent()*level + 10
            maxwidth = max(maxwidth, width)
            lastheight += H + 6
            
            maxwidth, lastheight = self.GetMaxSize2(child, level+1, 
                                                    maxwidth, lastheight)
            
            child, cookie = self.GetNextChild(item, cookie)

        return maxwidth, lastheight
    
#    def max_width(self):
#        dc = wx.ScreenDC()
#        dc.SetFont(self.GetFont())
#        widths = []
#        print dir(self)
#        for item, depth in self.__walk_items():
#            if item != self.root:
#                width = dc.GetTextExtent(self.GetItemText(item))[0] + self.GetIndent()*depth
#                widths.append(width)
#        return max(widths) + self.GetIndent()
         
#    def OnPaint(self,event):
#        self.AdapterSize()
        
#class ArbreIndicateursPrj(wx.CheckListBox):
#    def __init__(self, parent):
#        
#        wx.CheckListBox.__init__(self, parent, -1)
#        
#        self.parent = parent
#        
#        
#    
#        
##    ####################################################################################
##    def Construire(self, type_ens, competence = None):
##        dic = constantes.dicIndicateurs[competence]
##        clefs = dic.keys()
##        clefs.sort()
##        for k in clefs:
##            b = self.AppendItem(branche, k+" "+dic[k][0], ct_type=ct_type)
##            if len(dic[k])>1 and type(dic[k][1]) == dict:
##                self.Construire(b, dic[k][1], ct_type=1)
##            
##            if ct_type == 0:
##                self.SetItemBold(b, True)
#        
#    ####################################################################################
#    def OnItemCheck(self, event):
#        item = event.GetItem()
#        code = self.GetItemText(item).split()[0]
#        if item.GetValue():
#            self.parent.AjouterCompetence(code)
#        else:
#            self.parent.EnleverCompetence(code)
#        self.parent.SetCompetences()
#        event.Skip()
#
#    ####################################################################################
#    def traverse(self, parent=None):
#        if parent is None:
#            parent = self.GetRootItem()
#        nc = self.GetChildrenCount(parent, True)
#
#        def GetFirstChild(parent, cookie):
#            return self.GetFirstChild(parent)
#        
#        GetChild = GetFirstChild
#        cookie = 1
#        for i in range(nc):
#            child, cookie = GetChild(parent, cookie)
#            GetChild = self.GetNextChild
#            yield child
#            
#    ####################################################################################
#    def get_item_by_label(self, search_text, root_item):
#        item, cookie = self.GetFirstChild(root_item)
#    
#        while item != None and item.IsOk():
#            text = self.GetItemText(item)
#            if text.split()[0] == search_text:
#                return item
#            if self.ItemHasChildren(item):
#                match = self.get_item_by_label(search_text, item)
#                if match.IsOk():
#                    return match
#            item, cookie = self.GetNextChild(root_item, cookie)
#    
#        return wx.TreeItemId()      
            
####################################################################################
#
#   Classe définissant l'arbre de sélection du type d'enseignement
#
####################################################################################*

class ArbreTypeEnseignement(CT.CustomTreeCtrl):
    def __init__(self, parent, panelParent, 
                 pos = wx.DefaultPosition,
                 size = wx.DefaultSize,
                 style = wx.WANTS_CHARS):#|wx.BORDER_SIMPLE):

#        wx.Panel.__init__(self, parent, -1, pos, size)
        
        CT.CustomTreeCtrl.__init__(self, parent, -1, pos, (150, -1), style, 
                                   agwStyle = CT.TR_HIDE_ROOT|CT.TR_FULL_ROW_HIGHLIGHT\
                                   |CT.TR_HAS_VARIABLE_ROW_HEIGHT)#CT.TR_ALIGN_WINDOWS|CT.TR_HAS_BUTTONS|CCT.TR_NO_HEADER|T.TR_AUTO_TOGGLE_CHILD|\CT.TR_AUTO_CHECK_CHILD|\CT.TR_AUTO_CHECK_PARENT|
        self.Unbind(wx.EVT_KEY_DOWN)
        self.panelParent = panelParent
#        self.SetBackgroundColour(wx.WHITE)
        self.SetToolTip(wx.ToolTip(u"Choisir le type d'enseignement"))
        
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnClick)
#        self.Bind(wx.EVT_TREE_ITEM_COLLAPSING, self.OnItemCollapsed)
        
#        self.AddColumn(u"")
#        self.SetMainColumn(0)
        self.root = self.AddRoot("r")
        self.Construire(self.root)
        

        
        
    ######################################################################################  
    def Construire(self, racine):
        """ Construction de l'arbre
        """
#        print "Construire ArbreTypeEnseignement"
#        print ARBRE_REF
        self.branche = []
#        self.ExpandAll()
        for t, st in ARBRE_REF.items():
            if t[0] == "_":
                branche = self.AppendItem(racine, REFERENTIELS[st[0]].Enseignement[2])
            else:
                branche = self.AppendItem(racine, u"")#, ct_type=2)#, image = self.arbre.images["Seq"])
                rb = wx.RadioButton(self, -1, REFERENTIELS[t].Enseignement[0])
                self.Bind(wx.EVT_RADIOBUTTON, self.EvtRadioBox, rb)
                self.SetItemWindow(branche, rb)
                rb.SetToolTipString(REFERENTIELS[t].Enseignement[1])
                rb.Enable(len(REFERENTIELS[t].projets) > 0 or not self.panelParent.pourProjet)
                self.branche.append(branche)
            for sst in st:
                sbranche = self.AppendItem(branche, u"")#, ct_type=2)
                rb = wx.RadioButton(self, -1, REFERENTIELS[sst].Enseignement[0])
                self.Bind(wx.EVT_RADIOBUTTON, self.EvtRadioBox, rb)
                self.SetItemWindow(sbranche, rb)
                rb.SetToolTipString(REFERENTIELS[sst].Enseignement[1])
                rb.Enable(len(REFERENTIELS[sst].projets) > 0 or not self.panelParent.pourProjet)
                self.branche.append(sbranche)
        
        self.ExpandAll()
        self.CollapseAll()
        
    ######################################################################################              
    def EvtRadioBox(self, event):
        wnd = event.GetEventObject()
        for item in self.branche:
            if item.GetWindow() == wnd:# and item.GetParent()== self.root:
                self.OnClick(item = item)
                break
        
#        if event.GetEventObject().GetParent() == self.root:
#            self.OnClick(event)
        self.panelParent.EvtRadioBox(event)
        
        
    ######################################################################################              
    def SetStringSelection(self, label):
        for rb in self.branche:
            if isinstance(rb.GetWindow(), wx.RadioButton) and label == rb.GetWindow().GetLabel():
                rb.GetWindow().SetValue(True)
          
      
    ######################################################################################              
    def OnClick(self, event = None, item = None):
#        print "OnClick"
        if item == None:
            item = event.GetItem()
        else:
            self.SelectItem(item)
            
        if item.GetParent()== self.root:
            self.Freeze()
            self.CollapseAll()
            self.Expand(item)
            self.AdjustMyScrollbars()
            self.ScrollLines(1)
            self.ScrollLines(-1)
            self.Thaw()
#            self.Scroll()


    ######################################################################################              
    def CollapseAll(self):
#        print "CollapseAll"
        (child, cookie) = self.GetFirstChild(self.root)
        while child:
            self.Collapse(child)
#            self.CalculatePositions()
            child = self.GetNextSibling(child)
        self.RefreshSubtree(self.root)
#        self.GetMainWindow().AdjustMyScrollbars()
#        self.GetMainWindow().Layout()

 
    
    
    
###########################################################################################################
#
#  Liste de Checkbox
#
###########################################################################################################
        
class ChoixCompetenceEleve(wx.Panel):
    def __init__(self, parent, indic, projet, tache):
        wx.Panel.__init__(self, parent, -1)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.indic = indic
        self.parent = parent
        
        cb = []
        for e in projet.eleves:
            cb.append(wx.CheckBox(self, -1, ""))
            sizer.Add(cb[-1], 1, flag = wx.EXPAND)
            self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, cb[-1])
        self.cb = cb
        self.projet = projet
        self.tache = tache
        
        self.MiseAJour()
        self.Actualiser()
        self.Layout()
        self.SetSizerAndFit(sizer)
    


    #############################################################################
    def MiseAJour(self):
        """ Active/désactive les cases à cocher
            selon que les élèves ont à mobiliser cette compétence/indicateur
        """
#        print "MiseAJour", self.tache
        for i, e in enumerate(self.projet.eleves): 
            dicIndic = e.GetDicIndicateursRevue(self.tache.phase)
            comp = self.indic.split("_")[0]
            if comp in dicIndic.keys():
                if comp != self.indic: # Indicateur seul
                    indic = eval(self.indic.split("_")[1])
                    self.cb[i].Enable(dicIndic[comp][indic-1])
            else:
                self.cb[i].Enable(False)
#            self.cb[i].Update()
        
    #############################################################################
    def Actualiser(self):
        """ Coche/décoche les cases à cocher
            
        """
#        print "Actualiser", self.tache
#        self.CocherTout(self.indic in self.tache.indicateurs)
        
        for i in range(len(self.projet.eleves)):
            if self.cb[i].IsThisEnabled ():
                if i+1 in self.tache.indicateursEleve.keys():
                    indicateurs = self.tache.indicateursEleve[i+1]
                    self.cb[i].SetValue(self.indic in indicateurs)
      
            
#            comp = self.indic.split("_")[0]
#            if comp in dicIndic.keys():
#                if comp != self.indic: # Indicateur seul
#                    indic = eval(self.indic.split("_")[1])
#                    self.cb[i].SetValue(dicIndic[comp][indic-1])
#            else:
#                self.cb[i].SetValue(False)
#        self.CocherTout(self.indic in self.tache.indicateurs)
        
            
            
    #############################################################################
    def EvtCheckBox(self, event = None, eleve = None, etat = None):
        if event != None:
            cb = event.GetEventObject()
            eleve = self.cb.index(cb)+1
            etat = event.IsChecked()
        self.parent.MiseAJourCaseEleve(self.indic, etat, eleve, event != None)
        
    #############################################################################
    def CocherTout(self, etat):
        for cb in self.cb:
            if cb.IsEnabled():
                cb.SetValue(etat)
            
    #############################################################################
    def CocherEleve(self, eleve, etat, withEvent = False):
        if self.cb[eleve-1].IsEnabled():
            if etat != self.cb[eleve-1].GetValue():
                self.cb[eleve-1].SetValue(etat)
                if withEvent:
                    self.EvtCheckBox(eleve = eleve, etat = etat)
   
       
    #############################################################################
    def EstToutCoche(self):
        t = True
        for cb in self.cb:
            t = t and cb.GetValue() 
        return t
    
    #############################################################################
    def EstCocheEleve(self, eleve):
        return self.cb[eleve-1].GetValue() 
            


##
## Fonction pour vérifier si deux listes sont égales ou pas
##
#def listesEgales(l1, l2):
#    if len(l1) != len(l2):
#        return False
#    else:
#        for e1, e2 in zip(l1,l2):
#            if e1 != e2:
#                return False
#    return True





def get_key(dic, value, pos = None):
    """ Renvoie la clef du dictionnaire <dic> correspondant à la valeur <value>
    """
    i = 0
    continuer = True
    while continuer:
        if i > len(dic.keys()):
            continuer = False
        else:
            if pos:
                v = dic.values()[i][pos]
            else:
                v = dic.values()[i]
            if v == value:
                continuer = False
                key = dic.keys()[i]
            i += 1
    return key





####################################################################################
#
#   Classe définissant l'application
#    --> récupération des paramétres passés en ligne de commande
#
####################################################################################
class SeqApp(wx.App):
    def OnInit(self):
        wx.Log.SetLogLevel(0) # ?? Pour éviter le plantage de wxpython 3.0 avec Win XP pro ???
        
        fichier = ""
        if len(sys.argv)>1: # un paramétre a été passé
            parametre = sys.argv[1]

#           # on verifie que le fichier passé en paramétre existe
            if os.path.isfile(parametre):
                fichier = unicode(parametre, FILE_ENCODING)

        self.AddRTCHandlers()
        
        frame = FenetrePrincipale(None, fichier)
        frame.Show()
        
        if server != None:
            server.app = frame
        
        self.SetTopWindow(frame)
        
        
        return True

    def AddRTCHandlers(self):
        # make sure we haven't already added them.
        if rt.RichTextBuffer.FindHandlerByType(rt.RICHTEXT_TYPE_HTML) is not None:
            print u"AddRTCHandlers : déja fait"
            return
        
        # This would normally go in your app's OnInit method.  I'm
        # not sure why these file handlers are not loaded by
        # default by the C++ richtext code, I guess it's so you
        # can change the name or extension if you wanted...
        rt.RichTextBuffer.AddHandler(rt.RichTextHTMLHandler())
        rt.RichTextBuffer.AddHandler(rt.RichTextXMLHandler())

        # ...like this
        rt.RichTextBuffer.AddHandler(rt.RichTextXMLHandler(name="Autre XML",
                                                           ext="ox",
                                                           type=99))

        # This is needed for the view as HTML option since we tell it
        # to store the images in the memory file system.
        wx.FileSystem.AddHandler(wx.MemoryFSHandler())



##########################################################################################################
#
#  Dialogue de sélection d'URL
#
##########################################################################################################
class URLDialog(wx.Dialog):
    def __init__(self, parent, lien, pathseq):
        wx.Dialog.__init__(self, parent, -1)
        pre = wx.PreDialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        pre.Create(parent, -1, u"Sélection de lien")

        self.PostCreate(pre)

        sizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(self, -1, u"Sélectionner un fichier, un dossier ou une URL")
        label.SetHelpText(u"Sélectionner un fichier, un dossier ou une URL")
        sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, "Lien :")
#        label.SetHelpText("This is the help text for the label")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        url = URLSelectorCombo(self, lien, pathseq)
#        text.SetHelpText("Here's some help text for field #1")
        box.Add(url, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.url = url
        
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()
        
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(self)
            btnsizer.AddButton(btn)
        
        btn = wx.Button(self, wx.ID_OK)
        btn.SetHelpText("The OK button completes the dialog")
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btn.SetHelpText("The Cancel button cancels the dialog. (Cool, huh?)")
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)


    ######################################################################################  
    def GetURL(self):
        return self.url.GetPath()


    ######################################################################################  
    def OnPathModified(self, lien):
        return



    
class URLSelectorCombo(wx.Panel):
    def __init__(self, parent, lien, pathseq, dossier = True, ext = ""):
        wx.Panel.__init__(self, parent, -1)
        self.SetMaxSize((-1,22))
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.texte = wx.TextCtrl(self, -1, toSystemEncoding(lien.path), size = (-1, 16))
        if dossier:
            bt1 =wx.BitmapButton(self, 100, wx.ArtProvider_GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, (16, 16)))
            bt1.SetToolTipString(u"Sélectionner un dossier")
            self.Bind(wx.EVT_BUTTON, self.OnClick, bt1)
            sizer.Add(bt1)
        bt2 =wx.BitmapButton(self, 101, wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, (16, 16)))
        bt2.SetToolTipString(u"Sélectionner un fichier")
        self.Bind(wx.EVT_BUTTON, self.OnClick, bt2)
        self.Bind(wx.EVT_TEXT, self.EvtText, self.texte)
        
        self.ext = ext
        
        sizer.Add(bt2)
        sizer.Add(self.texte,1,flag = wx.EXPAND)
        self.SetSizerAndFit(sizer)
        self.lien = lien
        self.SetPathSeq(pathseq)

    # Overridden from ComboCtrl, called when the combo button is clicked
    def OnClick(self, event):
        
        if event.GetId() == 100:
            dlg = wx.DirDialog(self, u"Sélectionner un dossier",
                          style=wx.DD_DEFAULT_STYLE,
                          defaultPath = constantes.toSystemEncoding(self.pathseq)
                           #| wx.DD_DIR_MUST_EXIST
                           #| wx.DD_CHANGE_DIR
                           )
            if dlg.ShowModal() == wx.ID_OK:
                self.SetPath(dlg.GetPath())
    
            dlg.Destroy()
            
        else:
            dlg = wx.FileDialog(self, u"Sélectionner un fichier",
                                wildcard = self.ext,
                                defaultDir = constantes.toSystemEncoding(self.pathseq),
    #                           defaultPath = globdef.DOSSIER_EXEMPLES,
                               style = wx.DD_DEFAULT_STYLE
                               #| wx.DD_DIR_MUST_EXIST
                               #| wx.DD_CHANGE_DIR
                               )
    
            if dlg.ShowModal() == wx.ID_OK:
                self.SetPath(dlg.GetPath())
    
            dlg.Destroy()
        
        self.SetFocus()


    ##########################################################################################
    def EvtText(self, event):
        self.SetPath(event.GetString())


    ##########################################################################################
    def GetPath(self):
        return self.lien
    
    
    ##########################################################################################
    def SetPath(self, lien, marquerModifier = True):
        """ lien doit étre de type 'String' encodé en SYSTEM_ENCODING
            
        """
        self.lien.EvalLien(lien, self.pathseq)
        
        try:
            self.texte.ChangeValue(self.lien.path)
        except:
            self.texte.ChangeValue(toSystemEncoding(self.lien.path)) # On le met en SYSTEM_ENCODING
#        self.texte.ChangeValue(self.lien.path) 
#            self.texte.SetBackgroundColour(("white"))
#        else:
#            self.texte.SetBackgroundColour(("pink"))
        self.Parent.OnPathModified(self.lien, marquerModifier = marquerModifier)
        
        
    ##########################################################################################
    def SetPathSeq(self, pathseq):
        self.pathseq = pathseq


#############################################################################################################
#
# A propos ...
# 
#############################################################################################################
class A_propos(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, u"A propos de "+ version.__appname__)
        
        self.app = parent
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        titre = wx.StaticText(self, -1, " "+version.__appname__)
        titre.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD, False))
        titre.SetForegroundColour(wx.NamedColour("BROWN"))
        sizer.Add(titre, border = 10)
        sizer.Add(wx.StaticText(self, -1, "Version : "+version.__version__+ " "), 
                  flag=wx.ALIGN_RIGHT)
#        sizer.Add(wx.StaticBitmap(self, -1, Images.Logo.GetBitmap()),
#                  flag=wx.ALIGN_CENTER)
        
#        sizer.Add(20)
        nb = wx.Notebook(self, -1, style=
                             wx.BK_DEFAULT
                             #wx.BK_TOP 
                             #wx.BK_BOTTOM
                             #wx.BK_LEFT
                             #wx.BK_RIGHT
                             # | wx.NB_MULTILINE
                             )
        
        
        # Auteurs
        #---------
        auteurs = wx.Panel(nb, -1)
        fgs1 = wx.FlexGridSizer(cols=2, vgap=4, hgap=4)
        
        lstActeurs = ((u"Développement : ",(u"Cédrick FAURY", u"Jean-Claude FRICOU")),)#,
#                      (_(u"Remerciements : "),()) 


        for ac in lstActeurs:
            t = wx.StaticText(auteurs, -1, ac[0])
            fgs1.Add(t, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, border=4)
            for l in ac[1]:
                t = wx.StaticText(auteurs, -1, l)
                fgs1.Add(t , flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL| wx.ALL, border=4)
                t = wx.StaticText(auteurs, -1, "")
                fgs1.Add(t, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=0)
            t = wx.StaticText(auteurs, -1, "")
            fgs1.Add(t, flag=wx.ALL, border=0)
            
        auteurs.SetSizer(fgs1)
        
        # licence
        #---------
        licence = wx.Panel(nb, -1)
        try:
            txt = open(os.path.join(util_path.PATH, "gpl.txt"))
            lictext = txt.read()
            txt.close()
        except:
            lictext = u"Le fichier de licence (gpl.txt) est introuvable !\n\n" \
                      u"Veuillez réinstaller pySequence !"
            messageErreur(self, u'Licence introuvable',
                          lictext)
            
            
        wx.TextCtrl(licence, -1, lictext, size = (400, -1), 
                    style = wx.TE_READONLY|wx.TE_MULTILINE|wx.BORDER_NONE )
        

        
        # Description
        #-------------
        descrip = wx.Panel(nb, -1)
        t = wx.StaticText(descrip, -1,u"",
                          size = (400, -1))#,
#                        style = wx.TE_READONLY|wx.TE_MULTILINE|wx.BORDER_NONE) 
        t.SetLabelMarkup( wordwrap(u"<b>pySequence</b> est un logiciel d'aide à l'élaboration de séquences pédagogiques et à la validation de projets,\n"
                                          u"sous forme de fiches exportables au format PDF ou SVG.\n"
                                          u"Il est élaboré en relation avec les programmes et les documents d'accompagnement\n"
                                          u"des enseignements des filiéres STI2D, SSI et Technologie Collége",500, wx.ClientDC(self)))
        nb.AddPage(descrip, u"Description")
        nb.AddPage(auteurs, u"Auteurs")
        nb.AddPage(licence, u"Licence")
        
        sizer.Add(hl.HyperLinkCtrl(self, wx.ID_ANY, u"Informations et téléchargement : https://github.com/cedrick-f/pySequence",
                                   URL="https://github.com/cedrick-f/pySequence"),  
                  flag = wx.ALIGN_RIGHT|wx.ALL, border = 5)
        sizer.Add(nb)
        
        self.SetSizerAndFit(sizer)

#############################################################################################################
#
# ProgressDialog personnalisé
# 
#############################################################################################################
import win32gui
import win32con
class myProgressDialog(wx.ProgressDialog):
    def __init__(self, titre, message, maximum, parent, style = 0):
        wx.ProgressDialog.__init__(self, titre,
                                   message,
                                   maximum = maximum,
                                   parent = parent,
                                   style = style
                                    | wx.PD_APP_MODAL
                                    #| wx.PD_CAN_ABORT
                                    #| wx.PD_CAN_SKIP
                                    #| wx.PD_ELAPSED_TIME
                                    | wx.PD_ESTIMATED_TIME
                                    | wx.PD_REMAINING_TIME
                                    #| wx.PD_AUTO_HIDE
                                    )

#        hwnd = self.GetHandle()
#        exstyle = win32api.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
#        theStyle = win32con.HWND_TOPMOST
#        win32gui.SetWindowPos(hwnd, theStyle, 0, 0, 0, 0, win32con.SWP_NOSIZE|win32con.SWP_NOMOVE)
        
        

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
#        wx.CallAfter(self.top)
        
    def top(self):
        hwnd = self.GetHandle()
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                              win32con.SWP_NOSIZE | win32con.SWP_NOMOVE
                              ) 
        
    def OnClose(self, event):
        print "Close dlg"
        self.Destroy()        


#############################################################################################################
#
# Information PopUp
# 
#############################################################################################################
import cStringIO
import  wx.html as  html

class PopupInfo(wx.PopupWindow):
    def __init__(self, parent, page):
        wx.PopupWindow.__init__(self, parent, wx.BORDER_SIMPLE)
        self.parent = parent
      
        self.html = html.HtmlWindow(self, -1, size = (100,100),style=wx.NO_FULL_REPAINT_ON_RESIZE|html.HW_SCROLLBAR_NEVER)
        self.SetPage(page)
        self.SetAutoLayout(False)
        
        # Un fichier temporaire pour mettre une image ...
        self.tfname = tempfile.mktemp()
        #'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">'+

        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)
    
    ##########################################################################################
    def SetBranche(self, branche):
        self.branche = branche
        
    ##########################################################################################
    def XML_AjouterImg(self, node, item, bmp):
#        print "XML_AjouterImg"
        try:
            bmp.SaveFile(self.tfname, wx.BITMAP_TYPE_PNG)
        except:
            return
        
        img = node.getElementById(item)
        if img != None:
            td = node.createElement("img")
            img.appendChild(td)
            td.setAttribute("src", self.tfname)

        
    ##########################################################################################
    def OnDestroy(self, evt):
        if os.path.exists(self.tfname):
            os.remove(self.tfname)
            
    ##########################################################################################
    def SetPage(self, page):
#        self.SetSize((10,1000))
#        self.SetClientSize((100,1000))
#        self.html.SetSize( (100, 100) )
#        self.SetClientSize(self.html.GetSize())
        
        self.html.SetPage(page)
        ir = self.html.GetInternalRepresentation()

        self.SetClientSize((ir.GetWidth(), ir.GetHeight()))

        self.html.SetSize( (ir.GetWidth(), ir.GetHeight()) )

        
#        self.SetClientSize(self.html.GetSize())
#        self.SetSize(self.html.GetSize())
        
        
    ##########################################################################################
    def OnLeave(self, event):
        x, y = event.GetPosition()
        w, h = self.GetSize()
        if not ( x > 0 and y > 0 and x < w and y < h):
            self.Show(False)
        event.Skip()
        
        
        
        
        
class PopupInfo2(wx.PopupWindow):
    def __init__(self, parent, titre = "", doc = None, branche = None):
        wx.PopupWindow.__init__(self, parent, wx.BORDER_SIMPLE)
        self.parent = parent
        self.doc = doc
        self.branche = branche
        
        #
        # Un sizer "tableau", comme éa, on y met ce q'on veut oé on veut ...
        #
        self.sizer = wx.GridBagSizer()
        
        #
        # Un titre
        #
        self.titre = wx.StaticText(self, -1, titre)
        font = wx.Font(15, wx.SWISS, wx.NORMAL, wx.NORMAL)
        self.titre.SetFont(font)
        self.sizer.Add(self.titre, (0,0), flag = wx.ALL|wx.ALIGN_CENTER, border = 5)
        
        self.SetSizerAndFit(self.sizer)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)
        self.Bind(wx.EVT_LEFT_UP, self.OnClick)
        
    ##########################################################################################
    def SetBranche(self, branche):
        self.branche = branche
        
    ##########################################################################################
    def OnClick(self, event):
        if self.doc != None and self.branche != None:
            self.doc.SelectItem(self.branche)
            self.Show(False)
            
    ##########################################################################################
    def OnLeave(self, event):
        x, y = event.GetPosition()
        w, h = self.GetSize()
        if not ( x > 0 and y > 0 and x < w and y < h):
            self.Show(False)
        event.Skip()


    ##########################################################################################
    def SetTitre(self, titre):
        self.titre.SetLabel(titre)
        
        
    ##########################################################################################
    def CreerLien(self, position = (3,0), span = (1,1)):
        titreLien = wx.StaticText(self, -1, "")
        ctrlLien = wx.BitmapButton(self, -1, wx.NullBitmap)
        ctrlLien.Show(False)
        self.Bind(wx.EVT_BUTTON, self.OnClickLien, ctrlLien)
        sizerLien = wx.BoxSizer(wx.HORIZONTAL)
        sizerLien.Add(titreLien, flag = wx.ALIGN_CENTER_VERTICAL)
        sizerLien.Add(ctrlLien)
        self.sizer.Add(sizerLien, position, span, flag = wx.ALL, border = 5)
        return titreLien, ctrlLien

    ##########################################################################################
    def SetLien(self, lien, titreLien, ctrlLien):
        self.lien = lien # ATTENTION ! Cette faéon de faire n'autorise qu'un seul lien par PopupInfo !
        if lien.type == "":
            ctrlLien.Show(False)
            titreLien.Show(False)
            ctrlLien.SetToolTipString(toSystemEncoding(lien.path))
        else:
            ctrlLien.SetToolTipString(toSystemEncoding(lien.path))
            if lien.type == "f":
                titreLien.SetLabel(u"Fichier :")
                ctrlLien.SetBitmapLabel(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE))
                ctrlLien.Show(True)
            elif lien.type == 'd':
                titreLien.SetLabel(u"Dossier :")
                ctrlLien.SetBitmapLabel(wx.ArtProvider_GetBitmap(wx.ART_FOLDER))
                ctrlLien.Show(True)
            elif lien.type == 'u':
                titreLien.SetLabel(u"Lien web :")
                ctrlLien.SetBitmapLabel(images.Icone_web.GetBitmap())
                ctrlLien.Show(True)
            elif lien.type == 's':
                titreLien.SetLabel(u"Fichier séquence :")
                ctrlLien.SetBitmapLabel(images.Icone_sequence.GetBitmap())
                ctrlLien.Show(True)
            self.Layout()
            self.Fit()
        
    ##########################################################################################
    def OnClickLien(self, evt):
        if self.parent.typ == 'seq':
            path = self.parent.sequence.GetPath()
        else:
            path = self.parent.projet.GetPath()
        self.lien.Afficher(path, fenSeq = self.parent.parent)
        
    ##########################################################################################
    def CreerImage(self, position = (4,0), span = (1,1), flag = wx.ALIGN_CENTER):
        image = wx.StaticBitmap(self, -1, wx.NullBitmap)
        image.Show(False)
        self.sizer.Add(image, position, span, flag = flag|wx.ALL, border = 5)
        return image
    
    ##########################################################################################
    def SetImage(self, image, ctrlImage):
        if image == None:
            ctrlImage.Show(False)
        else:
            ctrlImage.SetBitmap(image)
            ctrlImage.Show(True)
        self.Layout()
        self.Fit()
        
    
    ##########################################################################################
    def CreerTexte(self, position = (1,0), span = (1,1), txt = u"", flag = wx.ALIGN_CENTER, font = None):
        if font == None:
            font = getFont_9()
        ctrlTxt = wx.StaticText(self, -1, txt)
        ctrlTxt.SetFont(font)
        self.sizer.Add(ctrlTxt, position, span, flag = flag|wx.ALL, border = 5)
        self.Layout()
        self.Fit()
        return ctrlTxt
    
    ##########################################################################################
    def CreerArbre(self, position = (1,0), span = (1,1), ref = None, dic = {}, flag = wx.ALIGN_CENTER):
        arbre = ArbreCompetencesPopup(self)
        self.sizer.Add(arbre, position, span, flag = flag|wx.ALL|wx.EXPAND, border = 5)
        self.Layout()
        self.Fit()
        return arbre
    
    ##########################################################################################
    def SetTexte(self, texte, ctrlTxt):
        if texte == "":
            ctrlTxt.Show(False)
        else:
            ctrlTxt.SetLabelMarkup(texte)
            ctrlTxt.Show(True)
            self.Layout()
            self.Fit()
    
    ##########################################################################################
    def CreerRichTexte(self, objet, position = (6,0), span = (1,1)):
        self.objet = objet # ATTENTION ! Cette faéon de faire n'autorise qu'un seul objet par PopupInfo !
        self.rtp = richtext.RichTextPanel(self, objet, size = (300, 200))
        self.sizer.Add(self.rtp, position, span, flag = wx.ALL|wx.EXPAND, border = 5)
        self.SetRichTexte()
        return self.rtp
    
    ##########################################################################################
    def SetRichTexte(self):
        self.rtp.Show(self.objet.description != None)
        self.rtp.Ouvrir()
        self.Layout()
        self.Fit()
        
    ##########################################################################################
    def DeplacerItem(self, item, pos = None, span = None):
        if item == None:
            item = self.titre
        if pos != None:
            self.sizer.SetItemPosition(item, pos) 
        if span != None:
            self.sizer.SetItemSpan(item, span) 
        
        







#############################################################################################################
#
# Dialog pour choisir le type de document à créer
# 
#############################################################################################################
class DialogChoixDoc(wx.Dialog):
    def __init__(self, parent,
                 style=wx.DEFAULT_DIALOG_STYLE 
                 ):

        wx.Dialog.__init__(self, parent, -1, u"Créer ...", style = style, size = wx.DefaultSize)
        self.SetMinSize((200,100))
        sizer = wx.BoxSizer(wx.VERTICAL)
        button = wx.Button(self, -1, u"Nouvelle Séquence")
        button.SetToolTipString(u"Créer une nouvelle séquence pédagogique")
        button.SetBitmap(images.Icone_sequence.Bitmap,wx.LEFT)
        self.Bind(wx.EVT_BUTTON, self.OnSeq, button)
        sizer.Add(button,0, wx.ALIGN_CENTRE|wx.ALL|wx.EXPAND, 5)
        
        button = wx.Button(self, -1, u"Nouveau Projet")
        button.SetToolTipString(u"Créer un nouveau projet")
        button.SetBitmap(images.Icone_projet.Bitmap,wx.LEFT)
        self.Bind(wx.EVT_BUTTON, self.OnPrj, button)
        sizer.Add(button,0,  wx.ALIGN_CENTRE|wx.ALL|wx.EXPAND, 5)
    
        self.SetSizer(sizer)
        sizer.Fit(self)
        
        self.SetReturnCode(0)
        

    def OnSeq(self, event):
        self.SetReturnCode(1)
        self.EndModal(1)

    def OnPrj(self, event):
        self.SetReturnCode(2)
        self.EndModal(2)

#import pywintypes


        
##########################################################################################################
#
#  Panel pour l'affichage des BO
#
##########################################################################################################
class Panel_BO(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.nb = wx.Notebook(self, -1)
        self.sizer.Add(self.nb, proportion=1, flag = wx.EXPAND)
        
        self.nb.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        
        self.SetSizer(self.sizer)
        
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)


    ######################################################################################################
    def OnEnter(self, event):
        self.SetFocus()
        event.Skip()
        
        
    ######################################################################################################
    def OnPageChanged(self, event):
        pass
    
    ######################################################################################################
    def Construire(self, ref):
        if ref.BO_dossier == u"":
            return
        
        wx.BeginBusyCursor()
        
        lst_pdf = []
        for d in ref.BO_dossier:
            path = os.path.join(util_path.BO_PATH, toFileEncoding(d))
            for root, dirs, files in os.walk(path):
                for f in files:
                    if os.path.splitext(f)[1] == r".pdf":
                        lst_pdf.append(os.path.join(root, f))
            
      
#        print self.nb.GetPageCount()
        for index in reversed(range(self.nb.GetPageCount())):
            try:
                self.nb.DeletePage(index)
            except:
                print "raté :", index
#        self.dataNoteBook.SendSizeEvent()
        
        
        for f in lst_pdf:
            page = genpdf.PdfPanel(self.nb)
            page.chargerFichierPDF(f)
            self.nb.AddPage(page, os.path.split(os.path.splitext(f)[0])[1])

        wx.EndBusyCursor()

              
##########################################################################################################
#
#  CodeBranche : conteneur du code d'un élément à faire figurer dans un arbre
#
##########################################################################################################
class CodeBranche(wx.Panel):
    def __init__(self, arbre, code = u""):
        wx.Panel.__init__(self, arbre, -1)
        sz = wx.BoxSizer(wx.HORIZONTAL)
        self.code = wx.StaticText(self, -1, code)
        sz.Add(self.code)
        self.SetSizerAndFit(sz)
        self.comp = {}

    def Add(self, clef, text = u""):
        self.comp[clef] = wx.StaticText(self, -1, "")
        self.GetSizer().Add(self.comp[clef])
        
    def SetLabel(self, text):
        self.code.SetLabel(text)
        
    def SetBackgroundColour(self, color):
        self.code.SetBackgroundColour(color)
    
    def SetToolTipString(self, text):
        self.code.SetToolTipString(text)
        
    def LayoutFit(self):
        self.Layout()
        self.Fit()
        
##########################################################################################################
#
#  DirSelectorCombo
#
##########################################################################################################
class DirSelectorCombo(wx.combo.ComboCtrl):
    def __init__(self, *args, **kw):
        wx.combo.ComboCtrl.__init__(self, *args, **kw)

        # make a custom bitmap showing "..."
        bw, bh = 14, 16
        bmp = wx.EmptyBitmap(bw,bh)
        dc = wx.MemoryDC(bmp)

        # clear to a specific background colour
        bgcolor = wx.Colour(255,254,255)
        dc.SetBackground(wx.Brush(bgcolor))
        dc.Clear()

        # draw the label onto the bitmap
        label = "..."
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        dc.SetFont(font)
        tw = dc.GetTextExtent(label)[0]
        dc.DrawText(label, (bw-tw)/2, (bw-tw)/2)
        del dc

        # now apply a mask using the bgcolor
        bmp.SetMaskColour(bgcolor)

        # and tell the ComboCtrl to use it
        self.SetButtonBitmaps(bmp, True)
        

    # Overridden from ComboCtrl, called when the combo button is clicked
    def OnButtonClick(self):
        # In this case we include a "New directory" button. 
#        dlg = wx.FileDialog(self, "Choisir un fichier modéle", path, name,
#                            "Rich Text Format (*.rtf)|*.rtf", wx.FD_OPEN)
        dlg = wx.DirDialog(self, _("Choisir un dossier"),
                           style = wx.DD_DEFAULT_STYLE
                           #| wx.DD_DIR_MUST_EXIST
                           #| wx.DD_CHANGE_DIR
                           )

        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it. 
        if dlg.ShowModal() == wx.ID_OK:
            self.SetValue(dlg.GetPath())

        # Only destroy a dialog after you're done with it.
        dlg.Destroy()
        
        self.SetFocus()

    # Overridden from ComboCtrl to avoid assert since there is no ComboPopup
    def DoSetPopupControl(self, popup):
        pass



        
#############################################################################################################
#
# Pour convertir les images en texte
# 
#############################################################################################################
import base64
try:
    b64encode = base64.b64encode
except AttributeError:
    b64encode = base64.encodestring
    
import tempfile

def img2str(img):
    """
    """
    global app
    if not wx.GetApp():
        app = wx.PySimpleApp()
        
    # convert the image file to a temporary file
    tfname = tempfile.mktemp()
    try:
        img.SaveFile(tfname, wx.BITMAP_TYPE_PNG)
        data = b64encode(open(tfname, "rb").read())
    finally:
        if os.path.exists(tfname):
            os.remove(tfname)
    return data



#############################################################################################################
#
# Message d'aide CI
# 
#############################################################################################################


class MessageAideCI(GMD.GenericMessageDialog):
    def __init__(self, parent):
        GMD.GenericMessageDialog.__init__(self,  parent, 
                                  u"Informations à propos de la cible CI",
                                  u"Informations à propos de la cible CI",
                                   wx.OK | wx.ICON_QUESTION
                                   #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                                   )
        self.SetExtendedMessage(u"Afin que tous les CI apparaissent sur la cible,\n"\
                                  u"ils doivent cibler des domaines (MEI)\n"\
                                  u"et des niveaux (FSC) différents.\n\n"\
                                  u"Les CI ne pouvant pas étre placés sur la cible\n"\
                                  u"apparaitront en orbite autour de la cible (2 maxi).\n\n"\
                                  u"Si le nombre de CI sélectionnés est limité à 2,\n"\
                                  u"le deuxiéme CI sélectionnable est forcément\n"\
                                  u"du méme domaine (MEI) que le premier\n"\
                                  u"ou bien un des CI en orbite.")
#        self.SetHelpBitmap(help)
        
        


