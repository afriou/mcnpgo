

#!/usr/bin/env python3

# @author Alexandre Friou

import sys,math
from copy import deepcopy
import numpy as np
import json
import re

# Keywords for cell cards
tsGCellKeyWords = ('trcl','*trcl','imp:e','imp:p','imp:n','imp','imp:n,p,e','u','fill','*fill','vol',\
    'wwn','pd','elpt','bflcl','unc','lat','nonu','tmp','cosy','pd','dxc','pwt','ext','fcl','$','&')

# Allowed particles for MX cards
tsGMxPart = ('n','h','p','t','s','a','d')


# Format for the writing of tr
FORMAT_TR = ".15e"
ROUND_TR = 14

def LectElem(lsLignesInput):
    """
    Function to store the file in a dictionary for processing.
    """

    # Formatting
    lsLignes = list()
    for i in lsLignesInput:
        if type(i) is list:
            lsLignes.extend(i)
        else:
            lsLignes.append(i)

    # Number of lines
    iNbLignesTot = len(lsLignes)

    # If the first line does not start with a comment, one is added
    if len(lsLignes[0]) == 1 and lsLignes[0].lower() != 'c':
        lsLignes[0] = 'c ' + lsLignes[0]
    if len(lsLignes[0]) > 1 and lsLignes[0].lower().startswith('c ') == False:
        lsLignes[0] = 'c ' + lsLignes[0]
    if len(lsLignes[0]) == 0:
        lsLignes[0] = 'c '

    # Init
    iFlagCell = 0
    iFlagCartes = 0
    iFlagGroupes = 0
    iIndGroupes = -1
    dictRes = dict()
    dictRes["fich"] = list()
    dictRes["surf"] = list()
    dictRes["cell"] = list()
    dictRes["trans"] = list()
    dictRes["matall"] = list()
    dictRes["mat"] = list()
    dictRes["matpn"] = list()
    for s in tsGMxPart:
        dictRes["matmx" + s] = list()
    dictRes["matmt"] = list()
    dictRes["saut"] = list()
    dictRes["englob"] = ''
    dictRes["mmcell"] = list()
    dictRes["mmsurf"] = list()
    dictRes["mmtrans"] = list()
    dictRes["groups"] = dict()

    # List that contains the output file
    strFichOut = list()
    tiSurf = list()
    tiCell = list()
    tiTrans = list()
    tiSaut = list()
    tiMatAll = list()
    tiMat = list()
    tiMatPN = list()
    tiMatMT = list()
    iIndFich = 0

    # Beginning of interpretation
    iFlagFinProc = 0
    i = 0
    while iFlagFinProc == 0:

        # Verif if end of file
        if i >= iNbLignesTot:
            iFlagFinProc = 1
            break

        # Current line
        sLC = lsLignes[i]
        i = i + 1

        if sLC != '' and sLC.isspace() == False \
            and sLC.startswith(('c ', 'C ')) == False and sLC[0].lower() != 'c':

            # List that contains the line for the output file
            strLignes = list()

            # Removing the ampersands
            sLC = sLC.replace('&',' ')

            # Placement in the output list
            strLignes.append(sLC)

            iFlagFinLigne = 0
            while iFlagFinLigne == 0:

                # Verif if end of file
                if i >= iNbLignesTot:
                    iFlagFinProc = 1
                    iFlagFinLigne = 1
                    tiSaut.append(iIndFich+1)
                    break

                # New line
                sLC = lsLignes[i]
                i = i + 1

                # If the next line is a comment or an instruction, we stop the
                if sLC == '' or sLC.isspace() == True \
                    or (sLC.startswith(('c ', 'C ')) == True and sLC[0].lower() == 'c'):

                    # Empty or comment line
                    iFlagFinLigne = 1
                    i = i - 1

                elif sLC[:5].isspace() == True:
                    # Continuation of the instruction
                    """
                    # If a closing parenthesis is present in the line
                    sTemp = sLC + ' '
                    if ')' in sTemp[:sTemp.find('$')] and '(' not in sTemp[:sTemp.find(')')]:
                        # Concatenation with the previous line
                        strLignes[-1] = strLignes[-1] + ' ' + sLC
                    else:
                        # Placement in the output list
                        strLignes.append(sLC)
                    """
                    # Placement in the output list
                    strLignes.append(sLC)

                else:
                    # New instruction
                    iFlagFinLigne = 1
                    i = i - 1

            if iFlagCell > 0:
                # Processing of surfaces
                strFichOut.append(strLignes)

                # To identify where the surface lines are
                tiSurf.append(iIndFich)
                iIndFich = iIndFich + 1

            elif iFlagCartes > 0:
                # Processing of cards
                strFichOut.append(strLignes)

                # Test if transfo
                sTemp = strLignes[0].lower().replace('*','')
                if sTemp.startswith('tr') == True:
                    # To identify where the transfo lines are
                    tiTrans.append(iIndFich)

                # Test if material
                sCard, sPart = GetCardType(sTemp)
                if sCard == 'm':
                    # To identify where the material lines are
                    tiMat.append(iIndFich)
                    tiMatAll.append(iIndFich)
                elif sCard == 'mpn':
                    # To identify where the material PN lines are
                    tiMatPN.append(iIndFich)
                    tiMatAll.append(iIndFich)
                elif sCard == 'mx':
                    # To identify where the material mx lines are

                    # Check if key exists
                    sKeyMX = "mat" + sCard + sPart
                    if sKeyMX not in dictRes.keys():
                        print(f"Warning: Unknown particle type for mx cards : {sTemp}")
                        print("This card will be ignored.")
                    else:
                        dictRes[sKeyMX].append(iIndFich)
                        tiMatAll.append(iIndFich)

                elif sCard == 'mt':
                    # To identify where the material mt lines are
                    tiMatMT.append(iIndFich)
                    tiMatAll.append(iIndFich)

                # Increment
                iIndFich = iIndFich + 1

            elif iFlagGroupes > 0:
                # Processing of groups
                iIndGroupes = i-1

                # We process the groups separately
                iFlagGroupes = -1
                break

            else:
                # Processing of cells
                strFichOut.append(strLignes)

                # To identify where the cell lines are
                tiCell.append(iIndFich)
                iIndFich = iIndFich + 1

        else:
            # We have encountered a blank line or a comment
            strFichOut.append([sLC])

            if len(sLC) == 0 or sLC.isspace() == True:
                tiSaut.append(iIndFich)
                if iFlagCell == 0:
                    # Line break, we move on to surfaces
                    iFlagCell = 1

                elif iFlagCell > 0:
                    # Line break, we move on to cards
                    iFlagCell = -1
                    iFlagCartes = 1

                elif iFlagCell < 0 and iFlagCartes > 0:
                    # Line break, we move on to groups
                    iFlagCell = -1
                    iFlagCartes = -1
                    iFlagGroupes = 1

                elif iFlagCell < 0 and iFlagCartes < 0 and iFlagGroupes < 0:
                    # End of file
                    break

            # Increment
            iIndFich = iIndFich + 1

    # Correction tiSaut
    if len(tiSaut) < 3:
        tiSaut.append(len(strFichOut))

    # Group management in the last part of the file
    dictGroupes = dict()
    iGroups = -1
    if iIndGroupes > 0 and iIndGroupes <= iNbLignesTot:
        # We construct the line to be interpreted
        iFinGroupes = iNbLignesTot
        i = iIndGroupes
        sLC = str()
        sLC_old = str()
        while i < iNbLignesTot:
            sLC_new = lsLignes[i]
            sLC = sLC + sLC_new
            i = i + 1
            if len(sLC_old) > 0 and ( len(sLC_new) == 0 or sLC_new.isspace() == True):
                # Line break
                iFinGroupes = i
                break

            # Old line
            sLC_old = sLC

        # Loading the groups
        if len(sLC.strip()) > 0:
            dictGroupes = json.loads(sLC)

            # Addition to the file
            #strFichOut.append(' ')
            strFichOut.append(lsLignes[iIndGroupes:iFinGroupes])

            # Identification of the groups
            iGroups = len(strFichOut) - 1

    # We retrieve the enclosing surface on the last cell
    dictGeo = GatherCellGeo(strFichOut[tiCell[-1]])
    sSurfEnglob = '(' + ' '.join(dictGeo["strgeo"]).strip() + ')'

    # Min/Max of cells, surfaces and transfo (useful for renaming)
    tiCellMinMax = list()
    iMax = GetLineNum(strFichOut[tiCell[0]][0])
    iMin = GetLineNum(strFichOut[tiCell[0]][0])
    for i in tiCell:
        iNumCell = GetCellNum(strFichOut[i][0])
        if iNumCell > 0:
            iMax = max(iMax,iNumCell)
            iMin = min(iMin,iNumCell)
    tiCellMinMax.append(iMin)
    tiCellMinMax.append(iMax)

    # First and last surface number
    tiSurfMinMax = list()
    iMax = GetLineNum(strFichOut[tiSurf[0]][0])
    iMin = GetLineNum(strFichOut[tiSurf[0]][0])
    for i in tiSurf:
        iNumSurf = GetLineNum(strFichOut[i][0])
        iMax = max(iMax,iNumSurf)
        iMin = min(iMin,iNumSurf)
    tiSurfMinMax.append(iMin)
    tiSurfMinMax.append(iMax)

    # First and last transfo number
    tiTransMinMax = list()
    if len(tiTrans) > 0:
        iMax = GetLineNum(strFichOut[tiTrans[0]][0])
        iMin = GetLineNum(strFichOut[tiTrans[0]][0])
        for i in tiTrans:
            iNumTr = GetLineNum(strFichOut[i][0])
            iMax = max(iMax,iNumTr)
            iMin = min(iMin,iNumTr)
        tiTransMinMax.append(iMin)
        tiTransMinMax.append(iMax)
    else:
        tiTransMinMax.append(0)
        tiTransMinMax.append(0)

    # Result
    dictRes["fich"] = strFichOut
    dictRes["surf"] = tiSurf
    dictRes["cell"] = tiCell
    dictRes["trans"] = tiTrans
    dictRes["matall"] = tiMatAll
    dictRes["mat"] = tiMat
    dictRes["matpn"] = tiMatPN
    dictRes["matmt"] = tiMatMT
    dictRes["saut"] = tiSaut
    dictRes["englob"] = sSurfEnglob
    dictRes["mmcell"] = tiCellMinMax
    dictRes["mmsurf"] = tiSurfMinMax
    dictRes["mmtrans"] = tiTransMinMax
    dictRes["groups"] = dictGroupes
    dictRes["ind_groups"] = iGroups

    return dictRes

def Renum(dictElem, tiListeInputCell, iStartCell, tiListeInputSurf, iStartSurf, iStartTrans):
    """
    Function to renumber the cells, surfaces and transformations of an input MCNP file.
    Does not modify dictElem.
    """

    # Assignment
    strFichOut = deepcopy(dictElem["fich"])
    tiSurf = deepcopy(dictElem["surf"])
    tiCell = deepcopy(dictElem["cell"])
    tiTrans = deepcopy(dictElem["trans"])
    dictGroupes = deepcopy(dictElem["groups"])
    iGroupes = dictElem["ind_groups"]

    # We now work on what we have read

    # Transfo
    # Unlike cells and surfaces, here we renumber all the transfos
    if iStartTrans > 0:
        # Init
        iNumTrRep = iStartTrans - 1
        tiNumTr = list()
        tiNumTrRep = list()

        # Renumbering of the cards
        for iIndTr in tiTrans:
            sLine = strFichOut[iIndTr][0]

            # Reading the number
            tiNumTr.append(GetCardNumber(sLine))

            # We replace iNumTr by iNumTrRep
            iNumTrRep = iNumTrRep + 1
            tiNumTrRep.append(iNumTrRep)

            # We change the number of the transfo
            strFichOut[iIndTr][0] = SwapTrCard(sLine,iNumTrRep)

        # We report the change to the cells
        for iIndCell in tiCell:

            UpdateCellTransform(strFichOut[iIndCell],'fill','num2num',tiNumTrRep,tiNumTr)
            UpdateCellTransform(strFichOut[iIndCell],'trcl','num2num',tiNumTrRep,tiNumTr)

        # We report the change to the surfaces
        for iIndSurf in tiSurf:
            sLine = strFichOut[iIndSurf][0]

            # Reading the transfo if present
            dictInfoSurf = GetSurfGeo(sLine)

            if dictInfoSurf["trans"] > 0:
                # Transfo present
                iNumTr = dictInfoSurf["trans"]

                # We look for the correspondence
                iNumTrRep = tiNumTrRep[tiNumTr.index(iNumTr)]

                # We change the number of the transfo
                strFichOut[iIndSurf][0] = SwapTrSurf(sLine,iNumTrRep)

        # We report the change to the groups
        if len(dictGroupes) > 0:
            for sKey in dictGroupes.keys():
                dictTemp = dictGroupes[sKey]

                # If the group has a category transfo
                if "trans" in dictTemp.keys():
                    tiTrNew = list()
                    for iNumTr in dictTemp["trans"]:

                        # We look for the correspondence
                        iNumTrRep = tiNumTrRep[tiNumTr.index(iNumTr)]

                        # New number
                        tiTrNew.append(iNumTrRep)

                    # We replace in the group
                    dictGroupes[sKey]["trans"] = tiTrNew

    # Cells
    if len(tiListeInputCell) > 0:
        # Init
        iNumCellRep = iStartCell - 1

        # Renumbering of the cells
        for iIndCell in tiCell:
            # We read the number of the cell
            # iNumCell = GetLineNum(strFichOut[iIndCell][0])
            iNumCell = GetCellNum(strFichOut[iIndCell][0])

            if iNumCell > 0 and (tiListeInputCell[0] == -1 or iNumCell in tiListeInputCell):
                # The cell is concerned by the filter

                # We will replace iNumCell by iNumCellRep
                iNumCellRep = iNumCellRep + 1

                # We report the change to the groups
                if len(dictGroupes) > 0:
                    for sKey in dictGroupes.keys():

                        # If the group has a cell category
                        if "cell" in dictGroupes[sKey].keys():
                            for iCellGroup in range(len(dictGroupes[sKey]["cell"])):
                                iNumCellGroup = dictGroupes[sKey]["cell"][iCellGroup]
                                if iNumCellGroup == iNumCell:
                                    dictGroupes[sKey]["cell"][iCellGroup] = iNumCellRep
                                elif iNumCellGroup == iNumCellRep:
                                    dictGroupes[sKey]["cell"][iCellGroup] = iNumCell

                # We change the number of the cell
                sLine = strFichOut[iIndCell][0]
                strFichOut[iIndCell][0] = str(iNumCellRep) + sLine[sLine.find(' '):]

                # We go through all the cells to change the numbers, the # and "like ... but"
                for iIndCell_Rep in tiCell:

                    # Number of the cell to be changed if the new number is
                    # already present, we interchange
                    if iIndCell != iIndCell_Rep:
                        sLine = strFichOut[iIndCell_Rep][0]

                        # Number of the cell
                        iCellLectCourant = GetCellNum(sLine)
                        if iCellLectCourant == iNumCellRep:
                            strFichOut[iIndCell_Rep][0] = str(iNumCell) + sLine[sLine.find(' '):]

                    # We go through the lines of the cell
                    for jSubLine in range(len(strFichOut[iIndCell_Rep])):

                        # Line read
                        sLine = strFichOut[iIndCell_Rep][jSubLine]
                        sLine = sLine + ' '

                        # We take into account the fact that 'like' can be found in a comment
                        sTemp = sLine.lower().split('$')

                        if sTemp[0].count('like') > 0:
                            # Number of the cell between like and but
                            iCellLectCourant = GetLikeBut(sLine)
                            if iCellLectCourant == iNumCell:
                                strFichOut[iIndCell_Rep][jSubLine] = sLine[:sLine.lower().find('like')+4] + ' ' + str(iNumCellRep) + ' ' + sLine[sLine.lower().find('but'):].rstrip()
                            elif iCellLectCourant == iNumCellRep:
                                strFichOut[iIndCell_Rep][jSubLine] = sLine[:sLine.lower().find('like')+4] + ' ' + str(iNumCell) + ' ' + sLine[sLine.lower().find('but'):].rstrip()

                        else:
                            # Verification
                            if '# ' in sLine:
                                print('ScriptRenum : syntax error "# "')
                                print(sLine)
                                return

                            # We replace or interchange
                            i = 0
                            while i < len(sLine):
                                if sLine[i] == '#' and sLine[i+1].isdigit() == True:
                                    sTemp = sLine[i+1:] + ' '
                                    iCellLectCourant = int(sTemp[:sTemp.find(' ')])

                                    if iCellLectCourant == iNumCell:
                                        strFichOut[iIndCell_Rep][jSubLine] = sLine[:i] + '#' + str(iNumCellRep) + sTemp[sTemp.find(' '):]
                                    elif iCellLectCourant == iNumCellRep:
                                        strFichOut[iIndCell_Rep][jSubLine] = sLine[:i] + '#' + str(iNumCell) + sTemp[sTemp.find(' '):]

                                # Update of sLine
                                sLine = strFichOut[iIndCell_Rep][jSubLine].rstrip()
                                i = i + 1

    # Surfaces
    if len(tiListeInputSurf) > 0:

        # Init
        iNumSurfRep = iStartSurf - 1

        # Renumbering of the surfaces
        for iIndSurf in tiSurf:

            # We read the number of surface
            iNumSurf = GetLineNum(strFichOut[iIndSurf][0])
            if tiListeInputSurf[0] == -1 or iNumSurf in tiListeInputSurf:
                # The surface is concerned by the filter

                # We replace iNumSurf by iNumSurfRep
                iNumSurfRep = iNumSurfRep + 1

                # We report the change to the groups
                if len(dictGroupes) > 0:
                    for sKey in dictGroupes.keys():

                        # If the group has a category surf
                        if "surf" in dictGroupes[sKey].keys():
                            for iSurfGroup in range(len(dictGroupes[sKey]["surf"])):
                                iNumSurfGroup = dictGroupes[sKey]["surf"][iSurfGroup]
                                if iNumSurfGroup == iNumSurf:
                                    dictGroupes[sKey]["surf"][iSurfGroup] = iNumSurfRep
                                elif iNumSurfGroup == iNumSurfRep:
                                    dictGroupes[sKey]["surf"][iSurfGroup] = iNumSurf

                # Line in progress
                sLine = strFichOut[iIndSurf][0]

                # We recopy * or + ...
                sSurfBoundary = ''
                for s in sLine.split()[0]:
                    if s.isdigit() == False:
                        sSurfBoundary = sSurfBoundary + s

                # We change the number of the surface
                strFichOut[iIndSurf][0] = sSurfBoundary + str(iNumSurfRep) + sLine[sLine.find(' '):]

                # We go through the surfaces remaining
                for iIndSurf_Rep in tiSurf:
                    # Number of the surface to be changed if the new number is
                    # already present, we interchange
                    if iIndSurf != iIndSurf_Rep:
                        sLine = strFichOut[iIndSurf_Rep][0]

                        # Number of the surface
                        iSurfLectCourant = GetLineNum(sLine)
                        if iSurfLectCourant == iNumSurfRep:
                            strFichOut[iIndSurf_Rep][0] = str(iNumSurf) + sLine[sLine.find(' '):]

                # We go through all the cells to change the surfaces
                for iIndSurf_Rep in tiCell:

                    # We take into account the fact that 'like' can be found in a comment
                    sTemp = strFichOut[iIndSurf_Rep][0].lower().split('$')

                    if sTemp[0].count('like') == 0:
                        for jSubLine in range(len(strFichOut[iIndSurf_Rep])):
                            # Recovery of the infos of the line
                            dictInfoLine = GetCellGeo(strFichOut[iIndSurf_Rep][jSubLine])

                            # We check if we have to renumber the surfaces
                            if len(dictInfoLine["surf"]) > 0:
                                # String of the parts to be replaced
                                sTemp = str(iNumSurf)
                                sTempRep = str(iNumSurfRep)

                                # Geometric part of the line
                                sLineCentre = dictInfoLine["strgeo"]

                                # Line review
                                iNbReplace = 0
                                if sLineCentre.count(sTemp) > 0 or sLineCentre.count(sTempRep) > 0:
                                    i = 0
                                    while i < len(sLineCentre):

                                        # Max index to avoid overflow
                                        iIndFinCheck = min(i+len(sTemp),len(sLineCentre))
                                        iIndFinCheckRep = min(i+len(sTempRep),len(sLineCentre))

                                        # We check if we are on sTemp or sTempRep
                                        iFlagNoReplace = 0
                                        if sLineCentre[i:iIndFinCheck] == sTemp:
                                            if ( (i+len(sTemp) < len(sLineCentre)) and sLineCentre[i+len(sTemp)].isdigit() ) \
                                                or ( (i-1 >= 0) and ( sLineCentre[i-1].isdigit() or sLineCentre[i-1] == '.' or sLineCentre[i-1] == '#') ):
                                                # It's not the right surface
                                                # We just checked if there is a number just before or after
                                                # or a point on the left or a #
                                                pass
                                            else:
                                                # It's the right surface, we replace
                                                sLineCentre = sLineCentre[:i] + sTempRep + sLineCentre[i+len(sTemp):]

                                                # We replaced iNumSurf, so we don't replace it again in the if that follows
                                                iFlagNoReplace = 1

                                                # On compte le nombre de remplacement fait
                                                iNbReplace = iNbReplace + 1
                                        # Ne pas mettre de elseif ici
                                        if sLineCentre[i:iIndFinCheckRep] == sTempRep and iFlagNoReplace == 0:
                                            if ( (i+len(sTempRep) < len(sLineCentre)) and sLineCentre[i+len(sTempRep)].isdigit() ) \
                                                or ( (i-1 >= 0) and ( sLineCentre[i-1].isdigit() or sLineCentre[i-1] == '.' or sLineCentre[i-1] == '#') ):
                                                # C'est pas la bonne surface
                                                # On vient de verifier si il y a un
                                                # nombre juste avant ou apres
                                                # ou un point a gauche ou un #
                                                pass
                                            else:
                                                # C'est la bonne surface, on remplace
                                                sLineCentre = sLineCentre[:i] + sTemp + sLineCentre[i+len(sTempRep):]

                                                # We count the number of replacements made
                                                iNbReplace = iNbReplace + 1

                                        # Increment
                                        i = i + 1
                                # Reconstruction of the line
                                if iNbReplace > 0:
                                    ## Formatting to align the line endings
                                    #sTemp = dictInfoLine["strdeb"] + '  ' + sLineCentre.strip()
                                    sLineFin = dictInfoLine["strfin"]
                                    sLineCom = dictInfoLine["strcom"]
                                    # We complete until we reach column 80
                                    #sLineFin = sLineFin.rjust(79-len(sTemp)) + '  ' + sLineCom
                                    #strFichOut[iIndSurf_Rep][jSubLine] = dictInfoLine["strdeb"] + ' ' + sLineCentre.strip() + ' ' + sLineFin

                                    strFichOut[iIndSurf_Rep][jSubLine] = dictInfoLine["strdeb"] + ' ' + sLineCentre.strip() + ' ' + sLineFin.strip() + ' ' + sLineCom.strip()

                            # We note if the line contains keywords
                            # If yes, the rest of the cell does not contain surfaces
                            if len(dictInfoLine['strfin']) > 0:
                                break

    # It should be placed in the reconstruction of the line here, outside the renumbering
    # The simplest thing is to redo GetCellGeo and update the line one last time with a formatting function
    # It would be better to pass the strFichOut list as input and the function would handle the rest

    # For the groups
    if len(dictGroupes) > 0:
        strFichOut[iGroupes] = json.dumps(dictGroupes)

    # The position of the cells, surfaces and tr remain the same
    dictOut = deepcopy(dictElem)
    dictOut["fich"] = deepcopy(strFichOut)

    return dictOut

def _Caveats(sFichier,geom):
    """
    This function checks the input file and prints warnings.
    """

    # Flag for printing name
    bFilePrinted = False

    # String for messages
    sFileGeom = f"In file: {geom}"

    # Expand tabs if necessary
    if '\t' in sFichier:
        sFichier = sFichier.replace('\t',' '*5)
        if bFilePrinted is False:
            print(sFileGeom)
            bFilePrinted = True
        print("Warning: tabs were converted to 5 spaces in file.")

    # Convert to list
    lsLignes = sFichier.splitlines()

    # Dealing with message block
    if lsLignes[0].lower().startswith("message"):
        if bFilePrinted is False:
            print(sFileGeom)
            bFilePrinted = True
        print("Warning: 'message:' block was deleted.")
        lsLignes = lsLignes[2:]

    # Caveats
    i = 0
    while i < len(lsLignes):
        # For end line issues and comment cards with only 'c'
        lsLignes[i] = lsLignes[i] + ' '

        # Correcting comments cards if necessary
        if IsComment(lsLignes[i]):
            if lsLignes[i].lower().startswith("c ") is False and lsLignes[i].lower().lstrip().startswith("c "):
                if bFilePrinted is False:
                    print(sFileGeom)
                    bFilePrinted = True
                print(f"Warning: line {i+1}, comment line has been left-stripped of blanks.")
                lsLignes[i] = lsLignes[i].lstrip()
        else:
            # This line is an instruction

            # Replace '# ' with '#', ...
            iComm = lsLignes[i].find('$')
            sLine = lsLignes[i][:iComm]
            for s in ['#']:
                ss = s + ' '
                while ss in sLine:
                    sLine = sLine.replace(ss,s)
                    if bFilePrinted is False:
                        print(sFileGeom)
                        bFilePrinted = True
                    print(f"Warning: spaces after '{s}' were deleted.")
            lsLignes[i] = sLine + lsLignes[i][iComm:] + ' '

            # Dealing with read lines
            if lsLignes[i].lstrip().lower().startswith("read"):
                if bFilePrinted is False:
                    print(sFileGeom)
                    bFilePrinted = True
                print(f"Warning: line {i+1}, 'read file' line has been commented.")
                lsLignes[i] = "c " + lsLignes[i].lstrip()

        # Dealing with ampersands
        if IsComment(lsLignes[i]) is False:
            if '&' in lsLignes[i].split('$')[0]:
                lsLignes[i] = lsLignes[i].replace('&','$')
                if  IsComment(lsLignes[i+1]) is False:
                    lsLignes[i+1] = " "*5 + lsLignes[i+1].strip()
                else:
                    if bFilePrinted is False:
                        print(sFileGeom)
                        bFilePrinted = True
                    print(f"Warning: line {i+1}, there may be an '&' before a comment line.")

        #  Comment line interrupting an instruction
        if IsComment(lsLignes[i]):
            if i < len(lsLignes)-1 and lsLignes[i+1].startswith(" "*5):
                if bFilePrinted is False:
                    print(sFileGeom)
                    bFilePrinted = True
                print(f"Error: line {i+1}, comment line within an instruction, please remove comment.")
                print("!!!! MCNP-GO will not function properly. !!!!")

        # Next line
        i = i+1

    return lsLignes

def ApplyTransfo(dictElemIn, lsInputTransfo0, sCommentTransfo):
    """
    Function to apply a transformation to an MCNP object
    Example: lsInputTransfo = ['tr',1,0,0,0,1,0,0,0,1,1]
    sCommentTransfo = '' : comment that will be added before the transform card
    The input transform is converted to cosinuses and forward transform if needed.
    """

    if type(lsInputTransfo0) != list:
        print('ApplyTransfo : Erreur, argument lsInputTransfo must be a list [,,]')
        return

    # Recopie
    dictElem = deepcopy(dictElemIn)

    # Convert cst transformation to cosinuses
    for iCell in dictElem["cell"]:
        UpdateCellTransform(dictElem["fich"][iCell],'fill','conv')
        UpdateCellTransform(dictElem["fich"][iCell],'trcl','conv')

    # Check transforms
    for i in dictElem["trans"]:
        for s in dictElem["fich"][i]:
            if 'j' in s.split('$')[0].lower():
                print("Error, jump cards 'j' are not supported for file transformations.")
                sys.exit()

    # Commentaire
    if len(sCommentTransfo) > 0:
        if sCommentTransfo.lower().startswith('c ') == False:
            sCommentTransfo = 'c ' + sCommentTransfo

    # Check de l'unite, conversion
    lsInputTransfo = ConvertTr(lsInputTransfo0)

    # On complete l'entree
    if len(lsInputTransfo0) <= 4:
        lsInputTransfo.extend([1,0,0, 0,1,0, 0,0,1])

    # Info sur les transfo
    dictObjetTr = GetObjetInfoTr(dictElem)

    # Attribution d'un numero
    i = 1
    iTrMax = 10000
    while i < iTrMax:
        if i not in dictObjetTr["numtr"]:
            iTr = i
            break
        i = i + 1

    # Verif
    if i == iTrMax:
        print('Transform: Error, problem when attributing a new transform number (>10000)')
        return

    # On regarde si toutes les surfaces possedent une transfo
    # Si non, on ajoute le numero de transfo
    iFlagTrAdd = 0
    for i in dictElem["surf"]:
        # Recuperation des infos surfaces
        sLine = dictElem["fich"][i][0]
        dictSurf = GetSurfGeo(sLine)

        if dictSurf["trans"] == 0:
            # Cette surface ne possede pas de transfo, on l'ajoute
            dictElem["fich"][i][0] = AddTrSurf(sLine,iTr)
            iFlagTrAdd = 1
        elif dictSurf["trans"] < 0:
            print('Error, no surface transformation is allowed for the periodic planes.')
            print(f'Surface: {sLine}')
            sys.exit()

    # Ajout d'une transfo dans les cartes
    if iFlagTrAdd > 0:
        lsLineTr = list()

        # Print de la carte + translation
        sTemp = lsInputTransfo[0] + str(iTr) + '  '
        for i in range(1,4):
            sTemp = sTemp + round(lsInputTransfo[i],ROUND_TR).__format__(FORMAT_TR) + ' '
        lsLineTr.append(sTemp)

        # Print de la matrice de rotation
        #if len(lsInputTransfo) > 4:
        for j in range(3):
            sTemp = '      '
            for i in range(4+j*3,7+j*3):
                sTemp = sTemp + round(lsInputTransfo[i],ROUND_TR).__format__(FORMAT_TR) + ' '
            lsLineTr.append(sTemp)

        # Print du dernier parametre
        if len(lsInputTransfo) == 14:
            lsLineTr.append('      ' + str(lsInputTransfo[13]))

        # Insertion de la carte a la suite des autres
        if dictObjetTr["nbtr"] == 0:
            # Si pas de carte tr, insertion au debut du bloc carte
            dictElem["trans"].append(dictElem["saut"][1] + 1)
            dictElem["fich"].insert(dictElem["trans"][0], lsLineTr)
        else:
            dictElem["fich"].insert(dictElem["trans"][-1] + 1, lsLineTr)
            dictElem["trans"].append(dictElem["trans"][-1] + 1) # ATTENTION, si d'autres categories de carte alors a mettre a jour aussi

    if dictObjetTr["nbtr"] > 0:

        # Modification des cartes tr existantes (sauf la derniere, si elle est nouvelle)
        if iFlagTrAdd > 0:
            lsNumTrans = dictElem["trans"][:-1]
        else:
            lsNumTrans = dictElem["trans"]

        # Boucle sur les transfo
        for iLine in lsNumTrans:
            dictTrCard = ReadTrCard(dictElem["fich"][iLine])

            # Conversion en scalaire
            dictTrCard = ConvertDictTr(dictTrCard)
            """
            if '*tr' in dictTrCard["strtr"].lower():
                dictTrCard["strtr"] = dictTrCard["strtr"].replace('*','')
                lsTemp = list()
                for i in dictTrCard["rot"]:

                    # if i == 90:
                    #     dVal = 0
                    # else:
                    #     dVal = math.cos(math.radians(i))
                    #     if abs(dVal) < 1e-8:
                    #         dVal = 0
                    #         print('La transfo n°' + str(dictTrCard["num"]) + ' possede une composante < 1e-8 radian, mise a zero')

                    dVal = math.cos(math.radians(i))
                    lsTemp.append(dVal)
                dictTrCard["rot"] = lsTemp
            """

            # Vector and matrix of read tr card
            npTransTr0 = np.array(dictTrCard["translat"])
            npMatTr0 = np.array(dictTrCard["rot"]).reshape(3,3)

            # Dealing with reverse transforms
            if dictTrCard["sens"] == -1:
                dictTrCard["sens"] = 1
                npTransTr0 = -npMatTr0.T.dot(npTransTr0)

            # Ajout de la partie rotation
            npMatInputTr = np.array(lsInputTransfo[4:13]).reshape(3,3)
            npMatTrNew = npMatTr0.dot(npMatInputTr)

            # Ajout de la partie translation
            tdTranslat = (npMatInputTr.transpose()).dot(npTransTr0.transpose()) \
                          + np.array(lsInputTransfo[1:4])

            # Print de la carte + translation
            lsLineTr = list()
            sTemp = dictTrCard["strtr"] + '  '
            for i in tdTranslat:
                sTemp = sTemp + round(i,ROUND_TR).__format__(FORMAT_TR) + ' '
            lsLineTr.append(sTemp)

            # Print de la matrice de rotation
            for j in range(3):
                sTemp = '      '
                for i in range(3):
                    sTemp = sTemp + round(npMatTrNew[j][i],ROUND_TR).__format__(FORMAT_TR) + ' '
                lsLineTr.append(sTemp)

            # Print du sens si vaut -1
            #if dictTrCard["sens"]  == -1:
            #    lsLineTr.append('      ' + str(dictTrCard["sens"]))

            # Mise a jour
            dictElem["fich"][iLine] = lsLineTr

    # Ajout de commentaires
    if len(sCommentTransfo) > 0:
        # Boucle sur les transfo
        iCountStart = 0
        for iLine in dictElem["trans"]:
            # Insertion du commentaire avant la carte
            dictElem["fich"].insert(iLine, sCommentTransfo)

            # Decalage des indices
            for iTrComment in range(iCountStart,len(dictElem["trans"])):
                dictElem["trans"][iTrComment] = dictElem["trans"][iTrComment] + 1
            iCountStart = iCountStart + 1

    # Modification des cartes trcl constantes
    dictCardUpdate = dict()
    dictCardUpdate["translat"] = lsInputTransfo[1:4]
    dictCardUpdate["rot"] = lsInputTransfo[4:13]
    dictCardUpdate["unit"] = 'scal'

    # Mise a jour des tr de cellule
    for sKey in ['trcl','fill']:
        for iCell in dictElem["cell"]:

            # Mise a jour de la description
            dictElem["fich"][iCell] = UpdateCellTransform(deepcopy(dictElem["fich"][iCell]),sKey,'cst_update',dictCardUpdate)

    # Mise a jour
    dictElemRes = LectElem(dictElem["fich"])

    return dictElemRes


def FormatImpOut(dictElemIn, imp='in'):
    """
    Fonction pour formatter correctement le fichier.
    Si "imp='out'", enleve les cartes "imp" et les mets dans le bloc des cartes.
    """

    # Recopie
    dictElem = deepcopy(dictElemIn)

    # Init dict des importances
    dictImp = dict()

    # Mise en forme des cellules
    iFlagImpLine = False # Flag for imp cards
    for i in dictElem["cell"]:
        lsNewLine = list()

        for j,sLigne in enumerate(dictElem["fich"][i]):

            # Info sur la ligne
            dictLigne = GetCellGeo(sLigne)

            # On fait le choix de ne pas preserver la mise en forme initiale
            if j == 0:
                sLineDeb = dictLigne["strdeb"].strip() + ' ' + ' '.join(dictLigne["strgeo"].split())
            else:
                sLineDeb = ' '*6 + ' '.join(dictLigne["strgeo"].split())
            sLineFin = dictLigne["strfin"].strip()
            sLineCom = dictLigne["strcom"].strip()

            # Gestion des importances
            if imp != 'in':
                # On enleve les cartes imp
                lsLineFinNew = list()
                for word in sLineFin.split():
                    if 'imp' not in word.lower():
                        lsLineFinNew.append(word)
                    else:
                        # Imp cards were seen
                        iFlagImpLine = True

                        # Lecture de la carte imp
                        sImpPartType = word[word.find(':')+1:word.find('=')]
                        sImpValue = word.split('=')[1].strip()

                        # On rempli le dictionnaire par type de particules
                        for s in sImpPartType.split(','):
                            if s not in dictImp.keys():
                                dictImp[s] = list()
                            dictImp[s].append(sImpValue)
                            # To be used later

                sLineFin = ' '.join(lsLineFinNew)


            # Fusion des bouts
            sLineDeb = sLineDeb + ' ' + sLineFin
            if len(sLineCom) > 0:
                sLineCom = ' '*(79-len(sLineDeb)) + sLineCom
            sLine = sLineDeb + ' ' + sLineCom

            if len(sLineDeb) == 0 or sLineDeb.isspace() == True:
                # Si ligne vide, on met un commentaire a la fin de la ligne precedente
                sLineCom = ' '*(79-len(lsNewLine[-1])) + sLineCom.strip()
                lsNewLine[-1] = lsNewLine[-1] + sLineCom
            else:
                lsNewLine.append(sLine)


        # Mise a jour
        dictElem["fich"][i] = lsNewLine



    # Mise en forme des surfaces et des cartes transfo
    for i in dictElem["surf"] + dictElem["trans"]:
        for j,sLigne in enumerate(dictElem["fich"][i]):

            # On met les commentaires a part
            if '$' in sLigne:
                sLineCom = sLigne[sLigne.find('$'):].strip()
                sLigne = sLigne[:sLigne.find('$')].rstrip()

                # Commentaires a la colonne 80
                sLineCom = ' '*(79-len(sLigne)) + sLineCom
            else:
                sLineCom = ''

            # Fusion
            dictElem["fich"][i][j] = sLigne + ' ' + sLineCom


    # Pas de mise en forme des cartes pour l'instant

    # ATTENTION :
    # A partir d'ici on supprime potentiellement des elements de dictElem["fich"],
    # donc les numerotations des lignes ne sont plus bonnes

    if imp != 'in':

        # On commence par supprimer les anciennes cartes imp si presentes
        lsListeIndexImp = list()
        for i in range(len(dictElem["fich"])):
            ligne = dictElem["fich"][i]

            if len(ligne[0].strip()) > 0:
                # A priori la carte imp est sur une ligne unique
                lsTemp = ligne[0].strip().split()
                s = lsTemp[0]
                if 'imp' in s.lower():
                    # On enregistre l'index
                    lsListeIndexImp.append(i)




        # On supprime les lignes
        for i in lsListeIndexImp.__reversed__():
            dictElem["fich"].pop(i)

        # Ajout des nouvelles cartes imp
        # Nombre de cellules
        iNbCell = len(dictElem["cell"])
        lsImpCard = list()
        #lsImpCard.append('c ' + '='*78)
        #lsImpCard.append('c ' + 'IMPORTANCES'.center(78))
        lsImpCard.append('c ' + '='*78)

        # If no cards were seen
        if iFlagImpLine == False:
            print("Warning: no cell imp cards were seen, assuming (n,p,e) importances of 1.")
            for sImpPartType in ['n','p','e']:
                dictImp[sImpPartType] = ['1']*(iNbCell-1) + ['0']


        for sImpPartType in dictImp.keys():
            # Verification
            if len(dictImp[sImpPartType]) != iNbCell:
                print(f"Warning: numbers of imp:{sImpPartType} cards not equal to number of cells (={iNbCell})")
                print("Building IMP card is not possible.")
                continue

            # Debut
            lsCurrentImpCard = list()
            lsCurrentImpCard.append(f'IMP:{sImpPartType}')

            # Boucle sur le reste
            iCountSame = 0
            for i,sImp in enumerate(dictImp[sImpPartType]):
                if i == 0:
                    sImpOld = sImp
                    lsCurrentImpCard.append(sImp)
                else:
                    if sImp == sImpOld:
                        # Same card as before
                        iCountSame = iCountSame + 1
                    else:
                        # Different importance
                        if iCountSame > 0:
                            lsCurrentImpCard.append(f"{iCountSame}r")

                        # Reset counter and add new value
                        iCountSame = 0
                        lsCurrentImpCard.append(sImp)

                    # Update value
                    sImpOld = sImp

            # Mise a jour
            lsImpCard.append(' '.join(lsCurrentImpCard))

        # Insertion des cartes
        iIndInsert = dictElem["saut"][1] + 1
        dictElem["fich"].insert(iIndInsert,lsImpCard)

    # Premiere interpretation du fichier pour reperer les groupes si présent
    dictElem = LectElem(dictElem["fich"])
    if dictElem["ind_groups"] > 0:
        iLigneLim = dictElem["ind_groups"]
    else:
        iLigneLim = len(dictElem["fich"])

    # Traitement des lignes trop longues
    for i in range(len(dictElem["fich"])):
        lsNewLine = list()
        for j in range(len(dictElem["fich"][i])):

            # Ligne courante
            sLine = dictElem["fich"][i][j]

            # Si ligne trop longue
            lsLongLine = list()
            sTemp = sLine
            if len(sLine) > 0 and sLine.isspace() == False \
            and sLine.lower().startswith(('c','c ')) == False: # carte cut ?
                # Si pas un commentaire, on traite

                sTempCheck = sTemp[:sTemp.find('$')].rstrip()
                while len(sTempCheck) >= 80:
                    iIndCut = sTemp[:75].rfind(' ')

                    # On coupe la ligne
                    sSep = ''
                    if '(' in sTemp[:iIndCut] and i < iLigneLim:
                        # En cas de parentheses, on utilise les &
                        sSep = ' &'
                    lsLongLine.append(sTemp[:iIndCut] + sSep)

                    # Mise a jour pour le prochain passage
                    if i < iLigneLim:
                        sTemp = '      ' + sTemp[iIndCut:].strip()
                    else:
                        sTemp = sTemp[iIndCut:].strip() # Pas d'espace en debut de ligne pour les groupes
                    sTempCheck = sTemp[:sTemp.find('$')].rstrip()

            # Fin de ligne
            lsLongLine.append(sTemp)
            lsNewLine.extend(lsLongLine)

        # Mise a jour
        dictElem["fich"][i] = lsNewLine

    # Mise a jour si besoin
    dictElem = LectElem(dictElem["fich"])

    return dictElem


def Extract(lsLignesInput, tiListeInputCell, radius, dictGroupes = dict()):
    """
    Fonction pour extraire une liste de cellule d'un element.
    Par defaut, une cellule englobante de rayon 20m est ajoute pour visualiser
    le fichier avec mcnp.
    Cette fonction peut etre utilise pour ensuite faire une insertion par cellule,
    l'insertion par surface englobante ne fonctionnant pas dans le cas general.
    """

    # Mise en forme
    lsLignes = list()
    for i in lsLignesInput:
        if type(i) is list:
            lsLignes.extend(i)
        else:
            lsLignes.append(i)

    # Nombre de lignes
    iNbLignesTot = len(lsLignes)

    # Init
    iFlagCell = 0
    tiNewCell = list()
    strCellules = list()
    tiNumCellFinal = list()
    iFlagCartes = 0
    tiListeSurface = list()
    strSurfaces = list()
    tiNumSurfFinal = list()
    tiMat = list()
    strMat = list()
    tiTrans = list()
    strTransfo = list()

    # Debut d'interpretation
    iFlagFinProc = 0
    i = 0
    while iFlagFinProc == 0:

        # Verif si fin de fichier
        if i >= iNbLignesTot:
            iFlagFinProc = 1
            break

        # Ligne courante
        sLC = lsLignes[i]
        i = i + 1

        if sLC != '' and sLC.isspace() == False:

            # Liste qui contient la ligne pour le fichier de sortie
            strLignes = list()

            # Rangement dans la liste de sortie
            strLignes.append(sLC)

            # Liste pour l interpretation de la ligne courante
            sLigne = str()

            iFlagInstr = 0
            if sLC.startswith(('c ', 'C ')) == False and sLC[0].lower() != 'c':
                # Si pas un commentaire on construit la ligne a interpreter
                iFlagInstr = 1

                # On enleve les commentaires
                temp = sLC.partition('$')
                sLC = temp[0]

                # Ligne a interpreter
                sLigne = sLigne + sLC


            iFlagFinLigne = 0
            while iFlagFinLigne == 0:

                # Verif si fin de fichier
                if i >= iNbLignesTot:
                    iFlagFinProc = 1
                    iFlagFinLigne = 1
                    break

                # Nouvelle ligne
                sLC = lsLignes[i]
                i = i + 1

                # Si la prochaine ligne est un commentaire ou une instruction, on arrete la
                if sLC == '' or sLC.isspace() == True:
                    # Ligne vide
                    iFlagFinLigne = 1
                    i = i - 1

                elif len(sLC) >= 5 and sLC[:5].isspace() == True:
                    # Instruction
                    iFlagInstr = 1

                    # Rangement dans la liste de sortie
                    strLignes.append(sLC)

                    # On enleve les commentaires
                    temp = sLC.partition('$')
                    sLC = temp[0]

                    # Ligne a interpreter
                    sLigne = sLigne + sLC

                elif sLC.startswith(('c ', 'C ')) == False and sLC[0].lower() != 'c':
                    # Instruction differente
                    if iFlagInstr == 0:
                        # Si on a jamais rencontre d instruction
                        # Rangement dans la liste de sortie
                        strLignes.append(sLC)

                        # On enleve les commentaires
                        temp = sLC.partition('$')
                        sLC = temp[0]

                        # Ligne a interpreter
                        sLigne = sLigne + sLC

                    else:
                        # Si deja instruction
                        iFlagFinLigne = 1
                        i = i - 1

                    iFlagInstr = 1

                else:
                    # Si pas instruction ni ligne vide, alors commentaire
                    if iFlagInstr == 1:
                        iFlagFinLigne = 1
                        i = i - 1
                    else:
                        # Rangement dans la liste de sortie
                        strLignes.append(sLC)


            #if iFlagFinProc == 1:
                #break

            if iFlagInstr == 1:
                if iFlagCell > 0:
                    # Traitements des surfaces
                    dictSurf = GetSurfGeo(sLigne)

                    # Lecture du numero des surfaces
                    iNumSurf = dictSurf["num"]

                    # Si la surface est dans la liste des surfaces a prendre, on ajoute sa description
                    if iNumSurf in tiListeSurface:
                        strSurfaces.append(strLignes)

                        # Ajout de la surface a la liste des numeros
                        tiNumSurfFinal.append(iNumSurf)

                        # Ajout du numero de tr
                        if dictSurf["trans"] > 0:
                            tiTrans.append(dictSurf["trans"])

                elif iFlagCartes > 0:
                    # Traitements des cartes

                    # Test si transfo
                    if sLigne.lower().startswith(('tr','*tr')) == True:
                        # Numero de la transfo
                        iNumTr = GetLineNum(sLigne)

                        if iNumTr in tiTrans:
                            # Transfo a prendre
                            strTransfo.append(strLignes)


                    # Test si materiau
                    sTemp = sLigne.lower()
                    if (sTemp.startswith('m') == True and sTemp[1].isdigit() == True)\
                        or sTemp.startswith(('mpn','mx','mt')) == True:
                        # Numero de la carte
                        iNumMat = GetLineNum(sTemp)

                        if iNumMat in tiMat:
                            # Materiau a prendre
                            strMat.append(strLignes)

                else:
                    # Traitements des cellules
                    dictCell = GetCellGeo(sLigne)

                    iNumCell = dictCell["num"]
                    if iNumCell in tiListeInputCell:
                        # La cellule est concerne par le filtre
                        strCellules.append(strLignes)

                        # Ajout de la cellule a la liste des numeros
                        tiNumCellFinal.append(iNumCell)

                        # Ajout des cellules, surfaces, materiaux
                        tiMat.extend(dictCell["mat"])
                        #tiNewCell.extend(dictCell["cell"])
                        # Pour ne pas prendre deux fois les memes cellules
                        # Dans certains cas rares seulement
                        for iNewCell in dictCell["cell"]:
                            if iNewCell not in tiNumCellFinal:
                                tiNewCell.append(iNewCell)
                        for dSurf in dictCell["surf"]:
                            tiListeSurface.append(abs(int(dSurf)))

                        # On recupere les eventuelles transfo
                        #tiNumTr = list()
                        UpdateCellTransform(deepcopy([sLigne]), 'fill', 'read', tiTrans)
                        UpdateCellTransform(deepcopy([sLigne]), 'trcl', 'read', tiTrans)
                        """
                        tiNumTr = GetCellTrcl(sLigne)
                        if len(tiNumTr) == 1:
                            # Il s'agit d'un numero de transfo
                            tiTrans.extend(tiNumTr)
                        """

        else:
            # On a rencontre une ligne blanche
            if iFlagCell == 0:
                if len(tiNewCell) == 0:
                    # Pas de nouvelles cellules a aller chercher
                    iFlagCell = 1
                else:
                    # On repart du debut du bloc cellule pour prendre en
                    # compte les nouvelles cellules

                    # Mise a jour de la liste
                    tiListeInputCellNew = list()
                    for iNC in tiNewCell:
                        if iNC not in tiListeInputCell:
                            tiListeInputCellNew.append(iNC)

                    if len(tiListeInputCellNew) == 0:
                        # Saut de ligne, on passe aux surfaces
                        iFlagCell = 1
                    else:
                        # On modifie la liste
                        tiListeInputCell = tiListeInputCellNew

                        # Rembobinage
                        i = 0

                        # Remise a zero
                        tiNewCell = list()

            elif iFlagCell > 0:
                # Fin du script
                iFlagCell = -1
                iFlagCartes = 1

    # Si pas de cellules trouvées
    if len(tiNumCellFinal) == 0:
        print("Extract: Error, provided cells are not found in file. Extract function will generate an empty object.")
        sys.exit()

    # Gestion des groupes
    dictGroupesExtract = dict()
    if len(dictGroupes) > 0:
        for sKey in dictGroupes.keys():
            d = dictGroupes[sKey]
            if "cell" in d.keys():
                tiGroupeExtract = list()
                for iGroup in d["cell"]:
                    # On recupere les numeros qui sont encore dans le nouvel objet
                    if iGroup in tiNumCellFinal:
                        tiGroupeExtract.append(iGroup)

                # Remplissage
                if len(tiGroupeExtract) > 0:
                    if sKey not in dictGroupesExtract:
                        dictGroupesExtract[sKey] = dict()
                    dictGroupesExtract[sKey]["cell"] = tiGroupeExtract

            if "surf" in d.keys():
                tiGroupeExtract = list()
                for iGroup in d["surf"]:
                    # On recupere les numeros qui sont encore dans le nouvel objet
                    if iGroup in tiNumSurfFinal:
                        tiGroupeExtract.append(iGroup)

                # Remplissage
                if len(tiGroupeExtract) > 0:
                    if sKey not in dictGroupesExtract:
                        dictGroupesExtract[sKey] = dict()
                    dictGroupesExtract[sKey]["surf"] = tiGroupeExtract

            if "trans" in d.keys():
                tiGroupeExtract = list()
                for iGroup in d["trans"]:
                    # On recupere les numeros qui sont encore dans le nouvel objet
                    if iGroup in tiTrans:
                        tiGroupeExtract.append(iGroup)

                # Remplissage
                if len(tiGroupeExtract) > 0:
                    if sKey not in dictGroupesExtract:
                        dictGroupesExtract[sKey] = dict()
                    dictGroupesExtract[sKey]["trans"] = tiGroupeExtract

            if "comment" in d.keys():
                if sKey in dictGroupesExtract:
                    dictGroupesExtract[sKey]["comment"] = d["comment"]


    # Construction du fichier de sortie
    lsFichierOut = list()

    # Numero de surface et de cellule max
    iMaxCell = max(tiNumCellFinal)
    iMaxSurf = max(tiNumSurfFinal)

    # Commentaires de debut de fichier
    for i in range(5):
        lsFichierOut.append('c ')

    # Ecriture des cellules
    lsFichierOut.extend(strCellules)

    # Construction du monde interieur
    # peut etre fait plus simplement avec un ' #'.join() ?
    sTemp = str(iMaxCell+1) + ' 0 '
    for iCell in tiNumCellFinal:
        sTemp = sTemp + '#' + str(iCell) + ' '
        if len(sTemp) + 10 > 80:
            lsFichierOut.append(sTemp)
            sTemp = '     '

    sTempFin = ' -' + str(iMaxSurf+1) + ' imp:P=1 imp:N=1 imp:E=1'
    if sTemp.isspace() == True:
        lsFichierOut.append(sTemp + sTempFin)
    else:
        lsFichierOut.append(sTemp)
        lsFichierOut.append('     ' + sTempFin)

    # Monde exterieur
    lsFichierOut.append(str(iMaxCell+2) + ' 0 ' + str(iMaxSurf+1) + ' imp:P=0 imp:N=0 imp:E=0')

    # Ligne vide
    lsFichierOut.append(' ')

    # Ecritures des surfaces
    lsFichierOut.extend(strSurfaces)

    # Surface du monde exterieur
    # A voir avec un mode d'extraction par cellules pour insertion par cellule
    # On peut aussi ignorer les deux dernieres cellules pour l'insertion par cellule
    lsFichierOut.append(str(iMaxSurf+1) + ' SO ' + str(radius))

    # Ligne vide
    lsFichierOut.append(' ')

    # Materiaux
    lsFichierOut.extend(strMat)

    # Transfo
    lsFichierOut.extend(strTransfo)

    # Ligne vide
    lsFichierOut.append(' ')

    # Groupes
    if len(dictGroupesExtract) > 0:
        lsFichierOut.append(json.dumps(dictGroupesExtract))

    # Interpretation du nouveau fichier
    dictOut = LectElem(lsFichierOut)

    return dictOut

def IsComment(sLine):
    """
    Fonction pour identifier si une ligne est un commentaire.
    """

    sLine = sLine.lower()
    if len(sLine) >= 5 and sLine[:5].isspace() == True:
        return False
    if len(sLine.lstrip()) == 1 and sLine.lstrip() == 'c':
        return True
    elif sLine.lstrip().startswith('c ') == True:
        return True
    else:
        return False


def GetKeyWordAsStr(sLine,sKey):
    """
    Fonction permettant de recuperer les entrees des mots clefs sur une ligne de cellules.
    Mot clef qui marchent : key = valeur.

    Retourne le début, le mot clef et la fin sous forme de string.

    sLineKey, sLineStart, sLineFin = GetKeyWordAsStr(sLine,sKey)
    """

    # Init
    sLineKey = ''
    sLineStart = ''
    sLineFin = ''
    sLine = sLine + ' ' # Pour eviter les cas particuliers de bout de ligne
    sLine0 = sLine
    sKey = sKey.lower()
    sLine = sLine.lower()

    # Verification si le mot est la
    if sLine.split('$')[0].count(sKey) == 0:
        return sLineKey, sLineStart, sLineFin

    # On repere les commentaires
    iCom = sLine.find('$')

    # On pourrait utiliser une regexp mais ca marche comme ca aussi
    iKey = sLine.find(sKey,0,iCom)
    iEgal = sLine.find('=',iKey)

    # On identifie ou est la fin
    iFinMin = len(sLine)
    for s in tsGCellKeyWords:
        iFin = sLine.find(s,iEgal)
        if iFin < iFinMin and iFin >= 0:
            iFinMin = iFin

    # Resultat
    sLineKey = sLine0[iEgal+1:iFinMin]
    sLineStart = sLine0[:iEgal+1]
    sLineFin = sLine0[iFinMin:]

    return sLineKey, sLineStart, sLineFin


def GetLikeBut(sLine):
    """
    Renvoie la cellule entre like et but sous forme d'un entier.
    """

    iNumCell = None
    if 'like' in sLine.split('$')[0].lower():
        iNumCell = int(re.search(r"like (\s*([0-9]+)\s*) but",sLine.lower()).group(1))
    return iNumCell


def GetCellMat(sLine):

    # Init
    res = list()
    sLine = sLine.lower()

    sTemp = sLine.split()
    if sTemp[1] == '0':
        res = [0, 0]
    else:
        res.append(int(sTemp[1]))
        res.append(float(sTemp[2]))

    return res

def SwapMatNumber(dictInput,iMatNumberNew,iMatNumber):
    """
    Echange un numero de carte materiau en le repercutant dans les cellules.
    Modifie dictInput.
    """

    # Check
    if iMatNumber == 0 or iMatNumberNew == 0:
        print('SwapMatNumber : Erreur, les materiaux ne doivent pas etre du vide.')
        return dictInput

    # On modifie le numero de la carte materiau
    lsKeys = ["matall"]
    for sKey in lsKeys:
        for iMatFich in dictInput[sKey]:
            lsCard = dictInput["fich"][iMatFich]
            iMat = GetCardNumber(lsCard[0])

            # Retrieve card and particle type
            sCard, sCardPart = GetCardType(lsCard[0])
            if len(sCardPart) > 0:
                sCardPart = ':' + sCardPart

            # Swap numbers
            if iMat == iMatNumber:
                dictInput["fich"][iMatFich][0] = sCard + str(iMatNumberNew) + sCardPart + lsCard[0][lsCard[0].find(' '):]
            elif iMat == iMatNumberNew:
                dictInput["fich"][iMatFich][0] = sCard + str(iMatNumber) + sCardPart + lsCard[0][lsCard[0].find(' '):]

    # On parcours les cellules
    for iCell in dictInput["cell"]:
        sLine = dictInput["fich"][iCell][0]
        dictCell = GetCellGeo(sLine)
        if dictCell["mat"][0] == iMatNumber:
            lsTemp = sLine.split(' ')
            dictInput["fich"][iCell][0] = lsTemp[0] + ' ' + str(iMatNumberNew) + ' ' + lsTemp[2] + ' ' \
                                          + dictCell["strgeo"] + ' ' + dictCell["strfin"] + ' ' + dictCell["strcom"]
        elif dictCell["mat"][0] == iMatNumberNew:
            lsTemp = sLine.split(' ')
            dictInput["fich"][iCell][0] = lsTemp[0] + ' ' + str(iMatNumber) + ' ' + lsTemp[2] + ' ' \
                                          + dictCell["strgeo"] + ' ' + dictCell["strfin"] + ' ' + dictCell["strcom"]


def GatherCellGeo(lsLine):
    """
    Pareil que GetCellGeo mais pour une liste.
    """

    Gres = dict()
    Gres["num"] = []
    Gres["mat"] = []
    Gres["strdeb"] = []
    Gres["strgeo"] = []
    Gres["strfin"] = []
    Gres["strcom"] = []
    Gres["cell"] = []
    Gres["surf"] = []
    iFlagFin = False
    for l in lsLine:
        res = GetCellGeo(l)

        # Cette partie n'a de sens que si la fin n'a pas encore ete atteinte
        if iFlagFin is False:
            Gres["num"].append(res["num"])
            Gres["mat"].extend(res["mat"])
            Gres["strdeb"].append(res["strdeb"])
            Gres["strgeo"].append(res["strgeo"])
            Gres["cell"].extend(res["cell"])
            Gres["surf"].extend(res["surf"])

        Gres["strfin"].append(res["strfin"])
        Gres["strcom"].append(res["strcom"])
        if len(res["strfin"]) > 0:
            # Si la fin est detectée, alors les lignes suivantes ne comporte que
            # des catégories fin et com
            iFlagFin = True

    return Gres

def GetCellGeo(sLine):
    """
    Recupere les elements geometriques de la cellule.
    res["num"] = 0       entier numero de cellule
    res["mat"] = []      liste numero du materiau et densite
    res["strdeb"] = ''   string de debut contenant numero, materiau ou rien
    res["strgeo"] = ''   string des surfaces et cellules
    res["strfin"] = ''   string de fin, contenant les mots clefs
    res["strcom"] = ''   string de commentaires, contenant les commentaires
    res["cell"] = []     liste des cellules sous format entier
    res["surf"] = []     liste des surfaces sous format float

    """

    #Init
    res = dict()
    res["num"] = 0
    res["mat"] = []
    res["strdeb"] = ''
    res["strgeo"] = ''
    res["strfin"] = ''
    res["strcom"] = ''
    res["cell"] = []
    res["surf"] = []
    sLine0 = sLine
    sLine = sLine.lower()

    # On rajoute des espaces pour interpreter correctement la ligne
    #sLine = sLine.replace('(',' ( ').replace(')',' ) ') # ne pas remplacer ':' par ' : ' pour le mot clef 'imp:'

    # Check si cellule avec like
    if 'like' in sLine:
        res["num"] = int(sLine[:sLine.find(' ')])
        sTemp = sLine[sLine.find('like')+4:sLine.find('but')]
        res["strdeb"] = sLine0[:sLine.find('like')+4]
        iComm = sLine.find('$')
        if iComm > 0:
            res["strfin"] = sLine0[sLine.find('but'):iComm].strip()
            res["strcom"] = sLine0[iComm:].strip()
        else:
            res["strfin"] = sLine0[sLine.find('but'):].strip()
        res["strgeo"] = sTemp
        res["cell"] = [int( sTemp.replace('&','') )]
        res["mat"] = [-1, -1]
        return res

    # Check si ligne de continuation
    if sLine.startswith('     ') == True :
        # Dans ce cas, pas de materiau
        iStart = 0
    else:
        # Numero de cellule
        temp = (sLine.replace('*','')).split()
        res["num"] = int(temp[0])

        # Materiau
        tiMat = GetCellMat(sLine)
        res["mat"] = tiMat

        # Indice de depart
        if tiMat[0] == 0:
            iStart = 2
        else:
            iStart = 3

    # On recupere la fin
    iFinMin = len(sLine)
    for i in tsGCellKeyWords:
        iFin = sLine.find(i)
        if iFin < iFinMin and iFin >= 0:
            iFinMin = iFin
    iComm = sLine.find('$')
    if iComm > 0:
        res["strfin"] = sLine0[iFinMin:iComm].strip()
        res["strcom"] = sLine0[iComm:].strip()
    else:
        res["strfin"] = sLine0[iFinMin:].strip()
        res["strcom"] = ''

    # Liste du debut
    strDeb = ''
    if iStart == 0:
        for i in sLine:
            if i.isspace() == True:
                strDeb = strDeb + ' '
            else:
                break
        res["strdeb"] = strDeb
    else:
        lsTempDeb = sLine0[:iFinMin].split()
        lsDeb = lsTempDeb[:iStart]

        # Partie debut sous forme de string
        strDeb = ' '.join(lsDeb)
        res["strdeb"] = strDeb

    # Liste de la partie geo
    lsTempGeo = sLine0[:iFinMin].split()
    lsGeo = lsTempGeo[iStart:]

    # Partie centrale sous forme de string
    strGeo = ' '.join(lsGeo)
    res["strgeo"] = strGeo

    # Verification
    if '# ' in sLine0:
        print("GetCellGeo: Syntax error '# ', hashtag must not be followed by a space.")
        print(sLine0)
        sys.exit()

    # Preparation pour recuperer les surfaces et cellules
    sTemp = strGeo.replace(')',' )') # pour prendre en compte '... #10) '
    lsTemp = sTemp.split()

    # On recupere les surfaces et cellules
    tiCell = list()
    tfSurf = list()
    sLineSurf = str()
    for i in lsTemp:
        if i.startswith('#') == True and i.startswith('#(') == False :
            # Cellule collee a #
            tiCell.append(int(i.replace('#',''))) # a terme ne prendre que les digits ?
        else:
            sLineSurf = sLineSurf + i + ' '

    # Menage
    sLineSurf = sLineSurf.replace(':',' ')
    sLineSurf = sLineSurf.replace('(',' ')
    sLineSurf = sLineSurf.replace(')',' ')
    sLineSurf = sLineSurf.replace('#',' ')

    # Recuperation des numeros des surfaces
    for i in sLineSurf.split():
        tfSurf.append(float(i))


    res["surf"] = tfSurf
    res["cell"] = tiCell

    return res

def GetSurfGeo(sLine):
    """
    Fonction recuperant le numero de surface et la transformee d'une ligne de surface
    res["num"] = 0    numero de la surface
    res["trans"] = 0  numero de transformation
    """

    # Init
    res = dict()
    res["num"] = 0
    res["trans"] = 0
    res["type"] = ''
    sLine = sLine.lower()

    # Surface number
    res["num"] = GetLineNum(sLine)

    # Transform number and type
    lsTemp = sLine.split()
    if lsTemp[1].replace('-','').replace('+','').isdigit():
        iTemp = int(lsTemp[1])

        # Transform numbers are positive
        # if iTemp > 0:
        #     res["trans"] = iTemp
        res["trans"] = iTemp

        # Third entry is surface type
        res["type"] = lsTemp[2]
    else:
        # Second entry is surface type
        res["type"] = lsTemp[1]

    return res


def GetCellNum(sLine):
    """
    Fonction recuperant le numero de la cellule.
    """

    # Init
    res = 0
    sLine = sLine.lower()

    #
    sTemp = sLine.replace('*','')
    lsTemp = sTemp.split()
    res = int(lsTemp[0])

    return res

def GetLineNum(sLine):
    """
    Fonction recuperant le premier numero de la ligne. Renvoie 0 si pas de numero
    """

    # Init
    res = 0
    sLine = sLine.lower()

    #
    sTemp = sLine.replace('*','')
    lsTemp = sTemp.split()

    sNum = str()
    for s in lsTemp[0]:
        if s.isdigit() == True:
            sNum = sNum + s

    if len(sNum) > 0:
        res = int(sNum)

    return res

def GetCardNumber(sLine):
    """
    Permet de recuperer le numero de la carte
    """

    # Init
    res = 0
    sLine = sLine.lower()

    lsTemp = sLine.split()
    lsTemp = lsTemp[0].split(':')

    sNum = str()
    for s in lsTemp[0]:
        if s.isdigit() == True:
            sNum = sNum + s

    if len(sNum) > 0:
        res = int(sNum)

    return res

def GetCardType(sLine):
    """
    Permet de recuperer le type de la carte et la particule si présente
    Par exemple renvoie 'mx' et 'p' pour 'mx5:p'
    """

    # Init
    sCard = str()
    sPart = str()

    lsTemp = sLine.split()
    lsTemp = lsTemp[0].split(':')

    # Card type
    for s in lsTemp[0]:
        if s.isalpha() == True:
            sCard = sCard + s

    # Particle type
    if len(lsTemp) == 2:
        sPart = lsTemp[1]

    return sCard, sPart


def GetObjetInfoTr(dictFich):
    """
    Fonction pour recuperer les infos de transformation d'un objet.
    res["numtr"] = ()   liste des entiers des numeros des cartes transfo
    res["nbtr"] = 0     nombres de cartes transfo
    """

    # Init
    res = dict()
    res["numtr"] = list()
    res["nbtr"] = 0

    iNbTr = 0
    if len(dictFich["trans"]) > 0:
        for i in dictFich["trans"]:
            res["numtr"].append(GetCardNumber(dictFich["fich"][i][0]))
            iNbTr = iNbTr + 1
    res["nbtr"] = iNbTr

    return res


def AddTrSurf(sLine,iTr):
    """
    Fonction pout ajouter un numero de transfo a une carte surface
    """

    # Init
    res = sLine

    dictSurf = GetSurfGeo(sLine)
    if dictSurf["trans"] > 0:
        print('AddTrSurf: Warning, surface card already possess a transformation')
        return res
    elif dictSurf["trans"] == 0:
        sTemp = ''
        if sLine.startswith('*'):
            sTemp = '*'
        elif sLine.startswith('+'):
            sTemp = '+'
        res = sTemp + str(dictSurf["num"]) + ' ' + str(iTr) + sLine[sLine.find(' '):]
    else:
        print('AddTrSurf: Error, surface transformation not allowed with periodic surfaces')
        print(sLine)
        return res


    return res


def ReadTrCard(lsLine):
    """
    Fonction qui interprete une carte transfo
    """

    # Init
    res = dict()
    res["num"] = 0
    res["unit"] = ''
    res["strtr"] = ''
    res["translat"] = list()
    res["rot"] = [1, 0, 0, 0, 1, 0, 0, 0, 1]
    res["sens"] = 1
    res["tr"] = list()

    # Unite
    sTemp = lsLine[0].strip()
    if sTemp[0] == '*':
        res["unit"] = 'deg'
    else:
        res["unit"] = 'scal'

    # Numero de carte
    res["num"] = GetCardNumber(lsLine[0])

    # Carte
    res["strtr"] = lsLine[0].split()[0]

    # Split
    sTemp = ''
    for s in lsLine:
        s = s + ' '
        sTemp = sTemp + s[:s.find('$')]
    lsTemp = sTemp.split()

    # Partie translation
    if len(lsTemp) < 4:
        print(f"ReadTrCard: Error, transform card {lsLine[0]} is ill-defined.")
        for s in lsLine:
            print(s)
        return
    else:
        tdTranslat = list()
        for i in range(1,4):
            tdTranslat.append(float(lsTemp[i]))
        res["translat"] = tdTranslat

    # Partie rotation
    if len(lsTemp) >= 5:
        tdRot = list()
        for i in range(4,13):
            tdRot.append(float(lsTemp[i]))
        res["rot"] = tdRot

    # Sens de la rotation
    if len(lsTemp) == 14:
        res["sens"] = int(lsTemp[13])

    # Sortie au format liste
    res["tr"] = [res["strtr"]] + res["translat"] + res["rot"] + [res["sens"]]

    return res


def UpdateTrclCstTrStr(sStart,sTemp,iFlagStar,listArgs):
    """
    Fonction pour mettre a jour une transfo cst.
    Agit sur une chaine de caractere quelconque.
    Pour les cartes trcl, qui n'ont qu'une seule entrée.
    """

    # Type d'arguments
    if listArgs[0] == 'cst_update':
        dictCard = listArgs[1]

        # Transfo a mettre
        npTransInput = np.array(dictCard["translat"])
        npMatInput = np.array(dictCard["rot"]).reshape(3,3)

    elif listArgs[0] == 'num2cst':
        ldictTrList = listArgs[1]
        liNumList = listArgs[2]

    elif listArgs[0] == 'cst2num':
        dictElem = listArgs[1]
        liAddTr = listArgs[2]

        # Info sur les transfo
        dictObjetTr = GetObjetInfoTr(dictElem)
        liAddTr.extend(dictObjetTr["numtr"])

    elif listArgs[0] == 'num2num':
        tiNumTrRep = listArgs[1]
        tiNumTr = listArgs[2]

    elif listArgs[0] == 'read':
        tiNumTrRead = listArgs[1]

    elif listArgs[0] == 'conv':
        # Convert from deg to cosinuses
        pass


    # Replace
    iFlagConv = False
    if '(' in sTemp:
        iPar1 = sTemp.find('(')
        iPar2 = sTemp.find(')')

        # Donnée entre parentheses
        sData = sTemp[iPar1+1:iPar2].strip()

        # Verification du contenu de la parenthese
        if len(sData.split()) > 1 and listArgs[0] == 'cst_update':
            # C'est une transfo
            iFlagConv = True

            # Remplacement
            sTemp = sTemp[:iPar1+1] + UpCstTr(sData,dictCard,iFlagStar,npTransInput,npMatInput) + sTemp[iPar2:]

        elif len(sData.split()) > 1 and listArgs[0] == 'cst2num':
            # C'est une transfo
            iFlagConv = True

            # Remplacement
            sTemp = CstTr2NumTr(sData,dictElem,liAddTr,iFlagStar)

        elif len(sData.split()) > 1 and iFlagStar == True and listArgs[0] == 'conv':
            # C'est une transfo
            iFlagConv = True

            # Convert transormation to cosinuses
            sTemp = sTemp[:iPar1+1] +  ConvCstTr(sData) + sTemp[iPar2:]

    else:
        # Une seule entrée qui doit etre un numéro de transfo
        sData = sTemp

        if len(sData.split()) == 1 and listArgs[0] == 'num2cst':
            # C'est un numero de transfo
            iFlagConv = True

            # Remplacement
            sTemp = '(' + NumTr2CstTr(sData,ldictTrList,liNumList) + ')'

        elif len(sData.split()) == 1 and listArgs[0] == 'num2num':
            # C'est un numero de transfo

            # On cherche la correspondance
            iNumTrRep = tiNumTrRep[tiNumTr.index(int(sData))]

            # Remplacement
            sTemp = str(iNumTrRep)

        elif len(sData.split()) == 1 and listArgs[0] == 'read':
            # C'est un numero de transfo

            # Ajout a la liste
            tiNumTrRead.append(int(sData))

    # On evite replace pour conserver la casse de la ligne
    if iFlagConv == True and '*trcl' in sStart.lower():
        iKey = sStart.lower().find('*trcl')
        sStart = sStart[:iKey] + ' trcl' + sStart[iKey+5:]

    return sStart + sTemp


def UpdateFillCstTrStr(sStart,sTemp,iFlagStar,listArgs):
    """
    Fonction pour mettre a jour une transfo cst.
    Agit sur une chaine de caractere quelconque.
    """

    # Type d'arguments
    if listArgs[0] == 'cst_update':
        dictCard = listArgs[1]

        # Transfo a mettre
        npTransInput = np.array(dictCard["translat"])
        npMatInput = np.array(dictCard["rot"]).reshape(3,3)

    elif listArgs[0] == 'num2cst':
        ldictTrList = listArgs[1]
        liNumList = listArgs[2]

    elif listArgs[0] == 'cst2num':
        dictElem = listArgs[1]
        liAddTr = listArgs[2]

        # Info sur les transfo
        dictObjetTr = GetObjetInfoTr(dictElem)
        liAddTr.extend(dictObjetTr["numtr"])

    elif listArgs[0] == 'num2num':
        tiNumTrRep = listArgs[1]
        tiNumTr = listArgs[2]

    elif listArgs[0] == 'read':
        tiNumTrRead = listArgs[1]

    elif listArgs[0] == 'conv':
        # Convert to cosinuses
        pass

    # Replace
    iFlagConv = False
    i = 0
    while i < len(sTemp):
        s = sTemp[i]

        if s == '(':
            iPar1 = i
            iPar2 = sTemp.find(')',i)

            # Donnée entre parentheses
            sData = sTemp[iPar1+1:iPar2].strip()

            # Verification du contenu de la parenthese
            if len(sData.split()) > 1 and listArgs[0] == 'cst_update':
                # C'est une transfo
                iFlagConv = True

                # Remplacement
                sTemp = sTemp[:iPar1+1] + UpCstTr(sData,dictCard,iFlagStar,npTransInput,npMatInput) + sTemp[iPar2:]

            elif len(sData.split())  == 1 and listArgs[0] == 'num2cst':
                # C'est un numero de transfo
                iFlagConv = True

                # Remplacement
                sTemp = sTemp[:iPar1+1] + NumTr2CstTr(sData,ldictTrList,liNumList) + sTemp[iPar2:]

            elif len(sData.split()) > 1 and listArgs[0] == 'cst2num':
                # C'est une transfo
                iFlagConv = True

                # Remplacement
                sTemp = sTemp[:iPar1+1] + CstTr2NumTr(sData,dictElem,liAddTr,iFlagStar) + sTemp[iPar2:]

            elif len(sData.split()) == 1 and listArgs[0] == 'num2num':
                # C'est un numero de transfo

                # On cherche la correspondance
                iNumTrRep = tiNumTrRep[tiNumTr.index(int(sData))]

                # Remplacement
                sTemp = sTemp[:iPar1+1] + str(iNumTrRep) + sTemp[iPar2:]

            elif len(sData.split()) == 1 and listArgs[0] == 'read':
                # C'est un numero de transfo

                # Ajout a la liste
                tiNumTrRead.append(int(sData))

            elif len(sData.split()) > 1 and iFlagStar == True and listArgs[0] == 'conv':
                # C'est une transfo
                iFlagConv = True

                # Convert transormation to cosinuses
                sTemp = sTemp[:iPar1+1] + ConvCstTr(sData) + sTemp[iPar2:]

        # Prochain caractere
        i = i + 1

    # On evite replace pour conserver la casse de la ligne
    if iFlagConv == True and '*fill' in sStart.lower():
        iKey = sStart.lower().find('*fill')
        sStart = sStart[:iKey] + ' fill' + sStart[iKey+5:]

    return sStart + sTemp

def UpCstTr(sData,dictCard,iFlagTrclDeg,npTransInput,npMatInput):
    """
    Fonction pour mettre a jour une tr cst.
    """

    # Les infos de la transfo en place
    tdTrCell = [float(ss) for ss in sData.split()]
    npTransCell = np.array(tdTrCell[0:3])

    # Verification
    if len(tdTrCell) < 3 or (len(tdTrCell) > 3 and len(tdTrCell) < 12):
        print("Warning : transform vector or matrix must be complete")
        print(f"Read transform: {tdTrCell}")
        sys.exit()

    # Completion ou conversion
    if len(tdTrCell) == 3:
        tdTrCell.extend([1,0,0, 0,1,0, 0,0,1])
    elif len(tdTrCell) > 3 and iFlagTrclDeg is True:
        # Conversion des degres en cosinus
        for i in range(3,12):
            tdTrCell[i] = math.cos(math.radians(tdTrCell[i]))
    npMatCell = np.array(tdTrCell[3:12]).reshape(3,3)

    # Dealing with reverse transforms
    if len(tdTrCell) > 12 and tdTrCell[12] == -1:
        tdTrCell[12] = 1
        npTransCell = -npMatCell.T.dot(npTransCell)

    # Matrice
    npMatTrNew = npMatCell.dot(npMatInput)
    npMatTrNew = npMatInput.transpose().dot(npMatTrNew)

    # Vecteur translation
    npTransCellNew = -npMatTrNew.transpose().dot(npTransInput) + npTransInput +\
        npMatInput.transpose().dot(npTransCell)

    # Elaboration de la string a mettre
    sTrCard = ''
    for d in npTransCellNew:
        sTrCard = sTrCard + round(d,ROUND_TR).__format__(FORMAT_TR) + ' '
    for ligne in npMatTrNew:
        for d in ligne:
            sTrCard = sTrCard + round(d,ROUND_TR).__format__(FORMAT_TR) + ' '


    return sTrCard


def NumTr2CstTr(sData,ldictTrList,liNumList):
    """
    Fonction pour passer d'un numero de Tr a sa valeur cst.
    """

    # Numero de la transfo
    iIndTr = liNumList.index(int(sData))

    # Elaboration de la string a mettre
    sTrCard = ' '.join([round(d,ROUND_TR).__format__(FORMAT_TR) for d in ldictTrList[iIndTr]['translat'] + ldictTrList[iIndTr]['rot']])

    return sTrCard

def CstTr2NumTr(sData,dictElem,liAddTr,iFlagStar):
    """
    Fonction pour remplacer une tr cst par un numero et ajouter une carte de
    transformée
    """

    # Unit of the card
    sUnit = ''
    if iFlagStar == True:
        sUnit = '*'

    # Max tr number
    iTrMax = 10000

    # Attribution d'un numero de tr
    j = 1
    while j < iTrMax:
        if j not in liAddTr:
            iTr = j
            break
        j = j + 1

    # Verif
    if j == iTrMax:
        print('Warning, transform number > 10000')

    # Transfo cst lue
    lTrans = [float(ss) for ss in sData.split()]

    # On vient creer une carte de transfo
    if len(lTrans) == 3:
        lTrans.extend([1,0,0,0,1,0,0,0,1])

    # Mise en forme de la carte
    lsLineTr = list()
    lsLineTr.append(sUnit + 'tr' + str(iTr) + ' ' + ' '.join([round(d,ROUND_TR).__format__(FORMAT_TR) for d in lTrans[0:3]]))
    lsLineTr.append(' '*6 + ' '.join([round(d,ROUND_TR).__format__(FORMAT_TR) for d in lTrans[3:6]]))
    lsLineTr.append(' '*6 + ' '.join([round(d,ROUND_TR).__format__(FORMAT_TR) for d in lTrans[6:9]]))
    lsLineTr.append(' '*6 + ' '.join([round(d,ROUND_TR).__format__(FORMAT_TR) for d in lTrans[9:]]))

    #lsLineTr = [f'{sUnit}tr{iTr} ' + sData]

    # Insertion de la carte a la suite des autres
    if len(liAddTr) == 0:
        # Si pas de carte tr, insertion au debut du bloc carte
        dictElem["trans"].append(dictElem["saut"][1] + 1)
        dictElem["fich"].insert(dictElem["trans"][0], lsLineTr)
    else:
        dictElem["fich"].insert(dictElem["trans"][-1] + 1, lsLineTr)
        dictElem["trans"].append(dictElem["trans"][-1] + 1) # ATTENTION, si d'autres categorie de carte alors a mettre a jour aussi

    # Ajout a la liste pour ne pas mettre deux fois le meme sur une meme ligne
    liAddTr.append(iTr)

    return str(iTr)


def ConvCstTr(sData):
    """
    Function to convert string transformation sData to cosinuses.
    """

    # Check for jump cards
    if 'j' in sData.lower():
        print('Error: jump cards are not allowed for cell transformation.')
        print(sData)
        sys.exit()

    # Init
    sRes = sData

    # Cast to list and convert
    lTrans = [float(ss) for ss in sData.split()]

    # Convert if matrix is here
    if len(lTrans) > 3:
        for i in range(3,min(12,len(lTrans))):
            lTrans[i] = math.cos(math.radians(lTrans[i]))

        # Convert back to string
        sRes = ' '.join([round(d,ROUND_TR).__format__(FORMAT_TR) for d in lTrans])

    return sRes

def UpdateCellTransform(lsLine,sKey,*wargs):
    """
    Prend en entree toute les lignes de la cellule.
    Met a jour une transfo de trcl ou fill selon les cas
    """

    # Variante selon les mots clefs
    if sKey.lower() == 'trcl':
        fctUpdate = UpdateTrclCstTrStr
    elif sKey.lower() == 'fill':
        fctUpdate = UpdateFillCstTrStr

    # Code similaire dans Renum
    iFlagFill = False
    iFlagStar = False
    for iLine,sLine in enumerate(lsLine):

        # Lecture des mots clefs si presents
        if iFlagFill == False:
            sLineKey, sLineStart, sLineFin = GetKeyWordAsStr(sLine,sKey)
            if '*' + sKey in sLineStart.lower():
                iFlagStar = True

                # Cas dans lequels on convertie le mot clef
                # if wargs[0] in ['conv','cst_update','num2cst','cst2num']:
                #     # On evite replace pour conserver la casse de la ligne
                #     iKey = sLineStart.lower().find('*' + sKey)
                #     sLineStart = sLineStart[:iKey] + ' ' + sKey + sLineStart[iKey+5:]
        else:
            if iFlagFill == True:
                # Detournement de GetCellGeo pour les sKey sur plusieurs lignes
                # Bricolage
                dLineFill = GetCellGeo(sLine)
                if len(dLineFill['strgeo']) > 0:
                    sLineKey = dLineFill['strgeo']

        # Mot clef present
        if len(sLineKey) > 0:
            # On update les transfo
            if iFlagFill == False:
                # Substitution
                sLine = fctUpdate(sLineStart,sLineKey,iFlagStar,wargs) + sLineFin
            else:
                sLine = fctUpdate(dLineFill['strdeb'],sLineKey,iFlagStar,wargs) \
                    + ' ' + dLineFill['strfin'] \
                    + ' ' + dLineFill['strcom']

            # Mise a jour ligne
            lsLine[iLine] = sLine

            # Fin de la carte
            if iFlagFill == True and len(dLineFill['strfin']) > 0:
                iFlagFill = False
            else:
                # Au cas où sKey continue sur plusieurs lignes
                iFlagFill = True

    return lsLine


def SetCstTrcl(dicElemIn):
    """
    Parcours un fichier et vient remplacer les cartes trcl par leur valeur
    de maniere a garder une coherence lors des transformations
    Prend en entree la sortie de LectElem
    """

    # Init
    dicElem = deepcopy(dicElemIn)
    liNumList = list()
    ldictTrList = list()

    # On parcourt les transfo
    for iTr in dicElem["trans"]:
        dictTr = ReadTrCard(dicElem["fich"][iTr])

        # Verification de l'unite et conversion si necessaire
        dictTr = ConvertDictTr(dictTr)
        # if 'deg' in dictTr["unit"]:
        #     lsRadRot = list()
        #     for i in dictTr["rot"]:
        #         """
        #         if i == 90 or i == -90:
        #             dVal = 0
        #         elif i == 180:
        #             dVal = -1
        #         elif i == -180:
        #             dVal = -1
        #         else:
        #         """
        #         dVal = math.cos(math.radians(i))

        #         lsRadRot.append(dVal)
        #     dictTr["rot"] = lsRadRot
        #     dictTr["unit"] = 'scal'

        # Remplissage des infos
        liNumList.append(dictTr["num"])
        ldictTrList.append(dictTr)


    # Parcourt du fichier
    for sKey in ['trcl','fill']:
        for iCell in dicElem["cell"]:

            # Mise a jour de la description
            dicElem["fich"][iCell] = UpdateCellTransform(deepcopy(dicElem["fich"][iCell]),sKey,'num2cst',ldictTrList,liNumList)

    return dicElem


def SwapCstTrclByNum(dictElemIn, addtr=list()):
    """
    Fonction pour remplacer les transformées de trcl et fill constante par un
    numéro de transformée. On ajoute une transformée au fichier.
    """

    # Init
    dictElem = deepcopy(dictElemIn)

    # On parcourt les cellules pour les cartes fill et trcl
    for sKey in ['trcl','fill']:
        for iCell in dictElem["cell"]:
            # Modifie dictElem
            UpdateCellTransform(dictElem["fich"][iCell],sKey,'cst2num',dictElem,addtr)

        # Mise a jour
        dictElem = LectElem(dictElem["fich"])

    return dictElem


def SwapTrSurf(sLine,iTr):
    """
    Fonction pour remplacer le numero d'une transfo d'une carte de surface
    """

    # Init
    res = sLine

    # On parcours la ligne
    for i in range(len(sLine)):
        if sLine[i].isalpha() == True:
            iIndAlpha = i
            break

    lsTemp = sLine.split()

    res = lsTemp[0] + ' ' + str(iTr) + ' ' + sLine[iIndAlpha:]
    return res



def SwapTrCard(sLine,iTr):
    """
    Fonction pour remplacer le numero d'une transfo d'une carte de transfo
    """

    # Init
    res = sLine

    # On trouve l'espace
    iSep = sLine.lstrip().find(' ')

    # On recopie *tr ou tr ...
    sTr = ''
    for s in sLine[:iSep]:
        if s.isdigit() == False:
            sTr = sTr + s

    # Reconstruction
    res = sTr + str(iTr) + sLine[iSep:]
    return res

def ConvertTr(lsInputTransfo0):
    """
    Converti en format scalaire une transfo
    """
    # Init
    lsInputTransfo = deepcopy(lsInputTransfo0)


    if '*' in lsInputTransfo0[0]:
        lsInputTransfo[0] = lsInputTransfo0[0].replace('*','')
        if len(lsInputTransfo0) > 4:
            for i in range(4,13):
                lsInputTransfo[i] = math.cos(math.radians(lsInputTransfo0[i]))

    return lsInputTransfo

def ConvertDictTr(dictTr0):
    """
    Converti en format scalaire une transfo.
    Prend en entrée la sortit de ReadTrCard.
    """
    # Init
    dictTr = deepcopy(dictTr0)


    if 'deg' in dictTr0["unit"]:
        for i in range(len(dictTr0["rot"])):
            dAngle = dictTr0["rot"][i]
            dictTr["rot"][i] = math.cos(math.radians(dAngle))
            """
            if dAngle == 90 or dAngle == -90:
                dVal = 0
            elif dAngle == 180:
                dVal = -1
            elif dAngle == 0:
                dVal = 1
            else:
                dictTr["rot"][i] = math.cos(math.radians(dAngle))
            """

        # Set unit to cosinuses
        dictTr["unit"] = "scal"
        dictTr["strtr"] = dictTr0["strtr"].replace('*','')

        # Sortie au format liste
        dictTr["tr"] = [dictTr["strtr"]] + dictTr["translat"] + dictTr["rot"] + [dictTr["sens"]]


    return dictTr

def ConcatCard(dictElem,sType):
    """
    Concatenation des cartes d'un certain type avec commentaires.
    Retourne une liste.
    """

    # Init
    lsCard = list()

    # Boucle sur les cartes
    for i in dictElem[sType]:

        # Insertion des commentaires precedent la carte
        lsCard.extend(GatherTopComments(dictElem["fich"],i))

        # Ajout de la carte
        lsCard.append(dictElem["fich"][i])

    return lsCard

def GatherTopComments(lsLine,i0):
    """
    Fonction pour récupérer les commentaires au dessus d'une carte.

    lsLine : list of list
    i0 : starting index

    Retourne une liste qui peut être vide.

    """

    # Init
    lsRes = list()

    # Verif
    if i0 == 0:
        return lsRes

    # Insertion des commentaires precedent la carte
    iFlagStop = 0
    iC = i0
    while iFlagStop == 0:
        iC = iC - 1
        if IsComment(lsLine[iC][0]) == False:
            # Fin des commentaires, on arrete
            iFlagStop = 1
            iC = iC + 1
            lsRes = lsLine[iC:i0]

    # Liste des commentaires
    return lsRes

def EulerZXZ(a=0,b=0,g=0,unit='deg',output=''):
    """
    Fonction retournant la matrice de passage composé d'une rotation selon l'axe
    Z, X' et Z''.
    La matrice est au format numpy.
    Ce code produit la matrice de passage M_A/B, B étant le repère après application
    des angles d'Euler.
    """

    # Unite
    if unit == 'deg':
        a_rad = math.radians(a)
        b_rad = math.radians(b)
        g_rad = math.radians(g)
    elif unit == 'rad':
        a_rad = a
        b_rad = b
        g_rad = g
    else:
        print(f"EulerZXZ: unknown unit (unit = {unit} ?).")
        sys.exit()

    # Elements de la matrice de rotation
    ca = math.cos(a_rad)
    sa = math.sin(a_rad)
    cb = math.cos(b_rad)
    sb = math.sin(b_rad)
    cg = math.cos(g_rad)
    sg = math.sin(g_rad)

    tdMat = [  ca*cg - sa*cb*sg,  sa*cg + ca*cb*sg, sb*sg,\
              -ca*sg - sa*cb*cg, -sa*sg + ca*cb*cg, sb*cg,\
               sa*sb           , -ca*sb           ,    cb]


    # Conversion en numpy
    if output == 'np':
        tdMat = np.reshape(np.array(tdMat),(3,3))

    return tdMat


def AnglesEulerZXZ(npMat):
    """
    Trouve les angles d'Euler de la matrice de passage composé d'une rotation
    selon l'axe    Z, X' et Z''.
    La matrice d'entrée est au format numpy.
    Ce code suppose que la matrice de passage est M_A/B, B étant le repère après
    application    des angles d'Euler.
    """

    # On commence par b
    b = np.arccos(npMat[2][2])

    # Ensuite a
    if abs(math.sin(b)) > 0:
        a = np.arctan2(npMat[0][2],-npMat[1][2])
    else:
        # A VALIDER CORRECTEMENT
        # Rotation pure selon Z
        a = -np.arctan2(-npMat[0][1],npMat[0][0])
        g = 0
        return a, b, g

    # Ensuite g de le meme maniere
    g = np.arctan2(npMat[2][0],npMat[2][1])


    return a, b, g


def RotU(u=[1,0,0],angle=0,unit='deg',output=''):
    """
    Fonction retournant la matrice de rotation d'un angle autour de l'axe u.
    Retourne la matrice est au format numpy et liste.
    Ce code produit la matrice de passage M_A/B, B étant le repère après application
    de la rotation.
    """

    # Unite
    if unit == 'deg':
        a_rad = math.radians(angle)
    elif unit == 'rad':
        a_rad = angle
    else:
        print(f"RotU: unknown unit (unit = {unit} ?).")
        sys.exit()

    # Normalisation de u
    dNorm = math.sqrt(u[0]**2 + u[1]**2 + u[2]**2)
    ux = u[0]/dNorm
    uy = u[1]/dNorm
    uz = u[2]/dNorm

    # Pour eviter de transposer la matrice
    a_rad = -a_rad

    # Elements de la matrice de rotation
    ca = math.cos(a_rad)
    sa = math.sin(a_rad)
    pmca = 1-ca

    tdMat = [ ca + ux*ux*pmca   ,  ux*uy*pmca - uz*sa,  ux*uz*pmca + uy*sa,\
              uy*ux*pmca + uz*sa,  ca + uy*uy*pmca   ,  uy*uz*pmca - ux*sa,\
              uz*ux*pmca - uy*sa,  uz*uy*pmca + ux*sa,  ca + uz*uz*pmca]

    """
    # Mise a zero des elements trop petits
    for i in range(len(tdMat)):
        if abs(tdMat[i]) < 1e-10:
            tdMat[i] = 0
    """
    # Conversion en numpy
    if output == 'np':
        tdMat = np.reshape(np.array(tdMat),(3,3))


    return tdMat