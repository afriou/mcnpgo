#!/usr/bin/env python3

# @author Alexandre Friou

import sys, math
from copy import deepcopy
import mcnpgo.mctk as tk
import numpy as np
import json

MCNP_FIRST_TALLY = dict()
MCNP_FIRST_TALLY["F1"] = 1
MCNP_FIRST_TALLY["F2"] = 2
MCNP_FIRST_TALLY["F3"] = 3
MCNP_FIRST_TALLY["F4"] = 4
MCNP_FIRST_TALLY["F5"] = 5
MCNP_FIRST_TALLY["F6"] = 6
MCNP_FIRST_TALLY["F7"] = 7
MCNP_FIRST_TALLY["F8"] = 8

class go:
    """
    Class for managing files/geometry objects.
    """

    def __init__(self, geom):
        # Path to the mcnp file
        self.geom = geom

        # Lists of inserted files
        self._InGeom = list()

        # Object transform
        self._Trans = ['tr',0,0,0, 1,0,0, 0,1,0, 0,0,1, 1]

        # List of transformations applied to the object
        self._FctTrans = []

        # Open file
        with open(geom,'r',errors='ignore') as fid:
            sFichier = fid.read()

            # Correct and check file for tabs, &, etc
            lsLignes = tk._Caveats(sFichier,geom)

        # Reading the element
        dictElem = tk.LectElem(lsLignes)
        self._dictElem = dictElem

        # For MCNP tally integration
        self._tiNumTally = dict()
        for s in MCNP_FIRST_TALLY.keys():
            self._tiNumTally[s] = list()
        self._tiTrTally = list()

    def __str__(self):
        """
        Display the properties of the object.
        """

        # Euler angles of the current file
        npMat = np.reshape(np.array(self._Trans[4:-1]),(3,3))
        dAngEulerA, dAngEulerB, dAngEulerG = tk.AnglesEulerZXZ(npMat)

        # Display a list of inserted objects
        lsPrint = list()
        lsPrint.append(' - Original file: ')
        lsPrint.append(self.geom)

        # List of transformations applied to the object
        if len(self._FctTrans) > 0:
            lsPrint.append(" "*5 + f"Applied translation: {self._Trans[1:4]}")
            lsPrint.append(" "*5 + f"Applied Euler angles: a={np.rad2deg(dAngEulerA)}, b={np.rad2deg(dAngEulerB)}, g={np.rad2deg(dAngEulerG)} " )
            lsPrint.append(" "*5 + "Rotation matrix: ")
            for i in range(3):
                lsPrint.append(" "*10 + f"{npMat[i]}")
            lsPrint.append(" "*5 + "List of applied transforms:")
            for i in range(len(self._FctTrans)):
                lsPrint.append(" "*10 + self._FctTrans[i])
        else:
            lsPrint.append(" "*5 + "No transforms were applied")
        lsPrint.append(' - Inserted files: ')
        lsPrint.extend(self._InGeom)

        # Final string
        sPrint = '\n'.join(lsPrint)

        return sPrint

    def ShowGroups(self):
        """
        ShowGroups():

        Display groups of the object.

        Example:
        obj.ShowGroups()
        """

        # We go through the keys, simple display
        print("Groupes de l'objet '" + self.geom + "' :")
        for sKeys in self._dictElem["groups"].keys():
            sPrint = "\t-" + sKeys

            # In case the group has a comment
            if "comment" in self._dictElem["groups"][sKeys].keys():
                sPrint = sPrint + ' (' + self._dictElem["groups"][sKeys]["comment"] + ')'

            # Display the group
            print(sPrint)

        return

    def GetGroup(self, sKey, sType):
        """
        GetGroup(sKey, sType):

        Retrieve the field of the group concerned.

        Example:
        mylist = obj.GetGroup("groupname","cell")
        """

        # If the keys exist, ok
        if sKey in self._dictElem["groups"].keys():
            if sType in self._dictElem["groups"][sKey].keys():
                return self._dictElem["groups"][sKey][sType]
            else:
                print(f"GetGroup: Warning, sub-group '{sType}' of group '{sKey}' not found.")
        else:
            print(f"GetGroup: Warning, group '{sKey}' not found")

        return list()

    def CheckGroup(self,sKey,sType):
        """
        CheckGroup(sKey,sType):

        Function to check the presence of a group in an object.
        Returns a boolean.

        Example:
        # Check if group "groupname" exists with a field "cell":
        obj.CheckGroup("groupname","cell")
        """

        if "groups" in self._dictElem:
            if sKey in self._dictElem["groups"].keys():
                if sType not in self._dictElem["groups"][sKey].keys():
                    print(f"CheckGroup: Warning, sub-group '{sType}' of group '{sKey}' not found.")
                    return False
                else:
                    return True
            else:
                print(f"CheckGroup: Warning, group '{sKey}' not found")
                return False
        else:
            print("CheckGroup: Warning, object does not contain any group.")
            return False

    def Insert(self, Elem, location = 'unknown', renum = 'no'):
        """
        Insert(Elem, location = 'unknown', renum = 'no'):

        Allows to insert an object into another by copying the enclosing surfaces.
        obj1.Insert(obj2)

        obj1 is modified to include obj2
        obj2 is not necessarily included entirely in obj1

        If obj2 is completely included in obj1, then the option location = 'inside'
        allows to optimize the calculation.
        If obj2 is completely outside of obj1, then the option location = 'outside'
        allows to optimize the calculation.

        The option "renum" allows to force the renumbering of "obj2", the calculation is then slower.

        Example:
        obj1.Insert(obj2, location = 'inside')
        obj1.Insert(obj2, location = 'inside', renum = 'yes') # force the renumbering of "obj2"

        """

        # Verification
        if location != 'unknown' and location != 'inside' and location != 'outside':
            print("Insert: Warning, unknown input for 'location', default mode chosen")
            location = 'unknown'
        if renum != 'yes' and renum != 'no':
            print("Insert: Warning, unknown input for 'renum', default mode chosen")
            renum = 'no'

        # It is necessary to renumber Elem
        # Add the description of the cell to self
        # Finally, we take everything into account, the new object contains everything
        # It is more practical when applying a transfo to the whole set

        # Euler angles of the inserted file
        npMat = np.reshape(np.array(Elem._Trans[4:4+9]),(3,3))
        dAngEulerA, dAngEulerB, dAngEulerG = tk.AnglesEulerZXZ(npMat)

        # List of inserted files
        self._InGeom.append(Elem.geom)

        # List of transformations applied to the inserted object
        if len(Elem._FctTrans) > 0:
            self._InGeom.append(" "*5 + f"Applied translation: {Elem._Trans[1:4]}")
            self._InGeom.append(" "*5 + f"Applied Euler angles: a={np.rad2deg(dAngEulerA)}, b={np.rad2deg(dAngEulerB)}, g={np.rad2deg(dAngEulerG)} " )
            self._InGeom.append(" "*5 + "Rotation matrix:")
            for i in range(3):
                self._InGeom.append(" "*10 + f"{npMat[i]}")
            self._InGeom.append(" "*5 + "List of applied transforms:")
            for i in range(len(Elem._FctTrans)):
                self._InGeom.append(" "*10 + Elem._FctTrans[i])
        else:
            self._InGeom.append(" "*5 + "No transforms was applied")

        # Files contained in the inserted object
        if len(Elem._InGeom) > 0:
            self._InGeom.append(" "*5 + ' - Files contained in ' + Elem.geom + ' :')
            for s in Elem._InGeom:
                self._InGeom.append(" "*6 + s)

        # Two cases depending on whether we renumber the newcomer or not
        if renum == 'yes':
            # Renumbering of Elem
            dictOut = tk.Renum(Elem._dictElem, [-1], 1, [-1], 1, 1)

            # Interpretation of the new element created
            dictOut = tk.LectElem(dictOut["fich"])
        else:
            # Interpretation of the incoming element
            dictOut = tk.LectElem(Elem._dictElem["fich"])

        # Two cases depending on whether we renumber or not
        if renum == 'yes':
            # Renumbering of self after Elem
            dictElem0 = tk.Renum(self._dictElem, [-1], dictOut["mmcell"][1]+1, [-1], dictOut["mmsurf"][1]+1, dictOut["mmtrans"][1]+1)

            # Interpretation of the new element created
            dictElem0 = tk.LectElem(dictElem0["fich"])
        else:

            # We create dictElem0
            dictElem0 = deepcopy(self._dictElem)

            # Verification if it is compatible
            if (dictOut["mmcell"][1] - self._dictElem["mmcell"][0])*(self._dictElem["mmcell"][1] - dictOut["mmcell"][0]) >= 0:
                # The elements have ranges with numbers in common
                # Renumbering of the cells
                dictElem0 = tk.Renum(dictElem0, [-1], dictOut["mmcell"][1]+1, [], -1, -1)
                dictElem0 = tk.LectElem(dictElem0["fich"])

            if (dictOut["mmsurf"][1] - self._dictElem["mmsurf"][0])*(self._dictElem["mmsurf"][1] - dictOut["mmsurf"][0]) >= 0:
                # The elements have ranges with numbers in common
                # Renumbering of the surfaces
                dictElem0 = tk.Renum(dictElem0, [], -1, [-1], dictOut["mmsurf"][1]+1, -1)
                dictElem0 = tk.LectElem(dictElem0["fich"])

            if (dictOut["mmtrans"][1] - self._dictElem["mmtrans"][0])*(self._dictElem["mmtrans"][1] - dictOut["mmtrans"][0]) >= 0:
                # The elements have ranges with numbers in common
                # Renumbering of the transfo
                dictElem0 = tk.Renum(dictElem0, [], -1, [], -1, dictOut["mmtrans"][1]+1)
                dictElem0 = tk.LectElem(dictElem0["fich"])

        # Merge of the material lists
        lsMatFusion = self._InsertMat(dictOut,Elem.geom) # dictOut is modified in the operation

        # Merge of the transformation cards
        lsTrCardFusion = tk.ConcatCard(dictOut,"trans")
        lsTrCardFusion.extend(tk.ConcatCard(dictElem0,"trans"))

        # Surface englobante de dictOut dans le groupe des sous-surfaces englobantes
        dictTemp = tk.GatherCellGeo(dictOut["fich"][dictOut["cell"][-1]]) # Derniere cellule
        iSubCell = tk.GetCellNum(dictOut["fich"][dictOut["cell"][-2]][0]) # Numero de la cellule diese
        if "subsurf" not in dictOut["groups"]:
            # Pas de surface englobante, on créé le groupe
            dictOut["groups"]["subsurf"] = dict()
            dictOut["groups"]["subsurf"]["surf"] = dictTemp["surf"]
            dictOut["groups"]["subsurf"]["cell"] = [iSubCell]
        else:
            # Il existe des surfaces englobantes, on rajoute celle de l'objet à la liste
            for iSurf in dictTemp["surf"]:
                if iSurf not in dictOut["groups"]["subsurf"]["surf"]:
                    dictOut["groups"]["subsurf"]["surf"].append(iSurf)
            if iSubCell not in dictOut["groups"]["subsurf"]["cell"]:
                dictOut["groups"]["subsurf"]["cell"].append(iSubCell)
        # Reperage des sections
        iIndCellFin = dictOut["cell"][-2]        # On enleve le monde exterieur
        iIndSurfDeb = dictOut["saut"][0] + 1     # +1 pour eviter la ligne blanche
        iIndSurfFin = dictOut["saut"][1]

        # Reperage des sections
        iIndCellFin0 = dictElem0["saut"][0]      # On garde le monde exterieur
        iIndSurfDeb0 = dictElem0["saut"][0] + 1  # +1 pour eviter la ligne blanche
        iIndSurfFin0 = dictElem0["saut"][1]

        # Concatenation des cellules
        lsElemNew = list()
        lsElemNew.extend(dictOut["fich"][:iIndCellFin+1])
        lsElemNew.extend(dictElem0["fich"][:iIndCellFin0])
        lsElemNew.extend(' ')

        # Concatenation des surfaces
        lsElemNew.extend(dictOut["fich"][iIndSurfDeb:iIndSurfFin])
        lsElemNew.extend(dictElem0["fich"][iIndSurfDeb0:iIndSurfFin0])
        lsElemNew.extend(' ')

        # Concatenation des cartes de transfo et de materiaux
        # The other cards are ignored
        lsElemNew.extend(lsTrCardFusion)
        lsElemNew.extend(lsMatFusion)
        lsElemNew.extend(' ')

        # Concatenation des groupes
        dictGroupsNew = deepcopy(dictOut["groups"])
        for sKey in dictElem0["groups"].keys():
            if sKey in dictGroupsNew.keys() and dictGroupsNew[sKey].keys() == dictElem0["groups"][sKey].keys():
                # If the group already exists, we concatenate the categories except comment
                if "cell" in dictGroupsNew[sKey].keys():
                    dictGroupsNew[sKey]["cell"].extend(dictElem0["groups"][sKey]["cell"])
                if "surf" in dictGroupsNew[sKey].keys():
                    dictGroupsNew[sKey]["surf"].extend(dictElem0["groups"][sKey]["surf"])
                if "trans" in dictGroupsNew[sKey].keys():
                    dictGroupsNew[sKey]["trans"].extend(dictElem0["groups"][sKey]["trans"])
            else:
                dictGroupsNew[sKey] = dictElem0["groups"][sKey]
        if len(dictGroupsNew) > 0:
            lsElemNew.append(json.dumps(dictGroupsNew))
        # CAS OU LES CLEFS SONT LES MEMES A RESOUDRE

        # Interpretation of the new element created
        dictElemNew = tk.LectElem(lsElemNew)

        if location == 'inside' or location == 'unknown':
            # Line diese of the object 1
            iCellDiese0 = dictElemNew["cell"][-2]
            dictDiese0 = tk.GetCellGeo(' '.join(dictElemNew["fich"][iCellDiese0]))

            # We reconstruct the diese line by adding the enclosing surface of the newcomer
            lsNewDiese = list()
            if len(dictElemNew["fich"][iCellDiese0]) == 1:
                lsNewDiese.append(dictDiese0["strdeb"].strip() + ' ' + dictDiese0["strgeo"].strip())
                lsNewDiese.append('      ' + dictOut["englob"].strip() + ' $ ' + Elem.geom)
                if len(dictDiese0["strfin"]) > 0 and dictDiese0["strfin"].isspace() == False:
                    lsNewDiese.append('      ' + dictDiese0["strfin"].strip() + ' ' + dictDiese0["strcom"])
                else:
                    lsNewDiese.append('c      ' + dictDiese0["strcom"])
            else:
                lsNewDiese.append(dictElemNew["fich"][iCellDiese0][0].strip())
                lsNewDiese.append('      ' + dictOut["englob"].strip() + ' $ ' + Elem.geom)
                for s in dictElemNew["fich"][iCellDiese0][1:]:
                    lsNewDiese.append('      ' + s.strip())
            dictElemNew["fich"][iCellDiese0] = lsNewDiese

        if location == 'outside' or location == 'unknown':
            # World line
            iCellMonde0 = dictElemNew["cell"][-1]
            dictMonde0 = tk.GetCellGeo(' '.join(dictElemNew["fich"][iCellMonde0]))

            # We reconstruct the world cell by adding the enclosing surface of the newcomer
            # Not necessarily necessary, but this allows to take into account overflows
            lsNewMonde = list()
            if len(dictElemNew["fich"][iCellMonde0]) == 1:
                lsNewMonde.append(dictMonde0["strdeb"].strip() + ' ' + dictMonde0["strgeo"].strip())
                lsNewMonde.append('      ' + dictOut["englob"].strip() + ' $ ' + Elem.geom)
                if len(dictMonde0["strfin"]) > 0 and dictMonde0["strfin"].isspace() == False:
                    lsNewMonde.append('      ' + dictMonde0["strfin"].strip() + ' ' + dictMonde0["strcom"])
                else:
                    lsNewMonde.append('c      ' + dictMonde0["strcom"])
            else:
                lsNewMonde.append(dictElemNew["fich"][iCellMonde0][0].strip())
                lsNewMonde.append('      ' + dictOut["englob"].strip() + ' $ ' + Elem.geom)
                for s in dictElemNew["fich"][iCellMonde0][1:]:
                    lsNewMonde.append('      ' + s.strip())
            dictElemNew["fich"][iCellMonde0] = lsNewMonde

        # Interpretation of the new element created
        dictElemNew = tk.LectElem(dictElemNew["fich"])

        # Last update
        self._dictElem = deepcopy(dictElemNew)

    def InsertCells(self, Elem):
        """
        InsertCells(Elem):

        Allows to insert the cells of an object 2 into an object 1:
        - obj1 is modified to include obj2
        - obj2 must be entirely included in obj1

        Insertion by cells is discouraged if your geometry contains bounding boxes.

        Example:
        obj1.InsertCells(obj2)

        """

        # It is necessary to renumber Elem
        # Add the description of the cell to self
        # Finally, we take everything into account, the new object contains everything
        # It is more practical when applying a transfo to the whole set

        # Euler angles of the inserted file
        npMat = np.reshape(np.array(Elem._Trans[4:4+9]),(3,3))
        dAngEulerA, dAngEulerB, dAngEulerG = tk.AnglesEulerZXZ(npMat)

        # List of inserted files
        self._InGeom.append(Elem.geom)

        # List of transformations applied to the inserted object
        if len(Elem._FctTrans) > 0:
            self._InGeom.append(" "*5 + f"Applied translation: {Elem._Trans[1:4]}")
            self._InGeom.append(" "*5 + f"Applied Euler angles: a={np.rad2deg(dAngEulerA)}, b={np.rad2deg(dAngEulerB)}, g={np.rad2deg(dAngEulerG)} " )
            self._InGeom.append(" "*5 + "Rotation matrix:")
            for i in range(3):
                self._InGeom.append(" "*10 + f"{npMat[i]}")
            self._InGeom.append(" "*5 + "List of applied transforms:")
            for i in range(len(Elem._FctTrans)):
                self._InGeom.append(" "*10 + Elem._FctTrans[i])
        else:
            self._InGeom.append(" "*5 + "No transforms was applied")

        # Files contained in the inserted object
        if len(Elem._InGeom) > 0:
            self._InGeom.append(" "*5 + ' - Files contained in ' + Elem.geom + ' :')
            for s in Elem._InGeom:
                self._InGeom.append(" "*6 + s)

        # Renumbering of Elem
        dictOut = tk.Renum(Elem._dictElem, [-1], 1, [-1], 1, 1)

        # Interpretation of the new element created
        dictOut = tk.LectElem(dictOut["fich"])

        # Renumbering of self after Elem
        dictElem0 = tk.Renum(self._dictElem, [-1], dictOut["mmcell"][1]+1, [-1], dictOut["mmsurf"][1]+1, dictOut["mmtrans"][1]+1)

        # Interpretation of the new element created
        dictElem0 = tk.LectElem(dictElem0["fich"])

        # Merge of the material lists
        lsMatFusion = self._InsertMat(dictOut,Elem.geom) # dictOut is modified in the operation

        # Merge of the transformation cards
        lsTrCardFusion = tk.ConcatCard(dictOut,"trans")
        lsTrCardFusion.extend(tk.ConcatCard(dictElem0,"trans"))

        # Reperage des sections
        if len(dictOut["cell"]) >= 3:
            iIndCellFin = dictOut["cell"][-3]        # On enleve le monde exterieur et la cellule diese
            iIndFin = -3
        else:
            iIndCellFin = dictOut["cell"][-2]        # On enleve le monde exterieur, a priori pas de cellule diese ici
            iIndFin = -2
        iIndSurfDeb = dictOut["saut"][0] + 1     # +1 pour eviter la ligne blanche
        iIndSurfFin = dictOut["saut"][1]

        # Reperage des sections
        iIndCellFin0 = dictElem0["saut"][0]      # On garde le monde exterieur
        iIndSurfDeb0 = dictElem0["saut"][0] + 1  # +1 pour eviter la ligne blanche
        iIndSurfFin0 = dictElem0["saut"][1]

        # Concatenation des cellules
        lsElemNew = list()
        lsElemNew.extend(dictOut["fich"][:iIndCellFin+1])
        lsElemNew.extend(dictElem0["fich"][:iIndCellFin0])
        lsElemNew.extend(' ')

        # Concatenation des surfaces
        lsElemNew.extend(dictOut["fich"][iIndSurfDeb:iIndSurfFin])
        lsElemNew.extend(dictElem0["fich"][iIndSurfDeb0:iIndSurfFin0])
        lsElemNew.extend(' ')

        # Concatenation des cartes de transfo et de materiaux
        # The other cards are ignored
        lsElemNew.extend(lsTrCardFusion)
        lsElemNew.extend(lsMatFusion)
        lsElemNew.extend(' ')

        # Concatenation des groupes
        dictGroupsNew = deepcopy(dictOut["groups"])
        for sKey in dictElem0["groups"].keys():
            if sKey in dictGroupsNew.keys() and dictGroupsNew[sKey].keys() == dictElem0["groups"][sKey].keys():
                # If the group already exists, we concatenate the categories except comment
                if "cell" in dictGroupsNew[sKey].keys():
                    dictGroupsNew[sKey]["cell"].extend(dictElem0["groups"][sKey]["cell"])
                if "surf" in dictGroupsNew[sKey].keys():
                    dictGroupsNew[sKey]["surf"].extend(dictElem0["groups"][sKey]["surf"])
                if "trans" in dictGroupsNew[sKey].keys():
                    dictGroupsNew[sKey]["trans"].extend(dictElem0["groups"][sKey]["trans"])
            else:
                dictGroupsNew[sKey] = dictElem0["groups"][sKey]
        if len(dictGroupsNew) > 0:
            lsElemNew.append(json.dumps(dictGroupsNew))
        # CAS OU LES CLEFS SONT LES MEMES A RESOUDRE

        # Interpretation of the new element created
        dictElemNew = tk.LectElem(lsElemNew)

        # Line diese
        iCellDiese0 = dictElemNew["cell"][-2]
        dictDiese0 = tk.GetCellGeo(' '.join(dictElemNew["fich"][iCellDiese0]))

        # Construction of the list of cells of the newcomer
        lsNumCellNew = list()
        for iCell in dictOut["cell"][:iIndFin+1]:
            iNumCell = tk.GetCellNum(dictOut["fich"][iCell][0])
            lsNumCellNew.append(str(iNumCell))

        sNumCellNew = '#' + ' #'.join(lsNumCellNew)
        # We reconstruct the diese line by adding the content of the diese line of the newcomer
        lsNewDiese = list()
        if len(dictElemNew["fich"][iCellDiese0]) == 1:
            lsNewDiese.append(dictDiese0["strdeb"].strip() + ' ' + dictDiese0["strgeo"].strip())
            lsNewDiese.append('      ' + sNumCellNew.strip() + ' $ ' + Elem.geom)
            if len(dictDiese0["strfin"]) > 0 and dictDiese0["strfin"].isspace() == False:
                lsNewDiese.append('      ' + dictDiese0["strfin"].strip() + ' ' + dictDiese0["strcom"])
            else:
                lsNewDiese.append('c      ' + dictDiese0["strcom"])
        else:
            lsNewDiese.append(dictElemNew["fich"][iCellDiese0][0].strip())
            lsNewDiese.append('      ' + sNumCellNew.strip() + ' $ ' + Elem.geom)
            for s in dictElemNew["fich"][iCellDiese0][1:]:
                lsNewDiese.append('      ' + s.strip())
        dictElemNew["fich"][iCellDiese0] = lsNewDiese

        # Interpretation of the new element created
        dictElemNew = tk.LectElem(dictElemNew["fich"])

        # Last update
        self._dictElem = deepcopy(dictElemNew)

    def Transform(self,lsInput, comment=''):
        """
        Transform(lsInput, comment=''):

        Allows to apply a transformation to a file.
        Takes as input the content of the MCNP transformation card.

        Example:
        obj.Transform(['tr',12,3,5]) # Translation only
        obj.Transform(['tr',12,3,5, 0,-1,0, 0,0,1, -1,0,0]) # Translation + rotation
        obj.Transform(['*tr',12,3,5, 90,180,90, 90,90,180, -180,90,90]) # Translation + rotation in degrees
        obj.Transform(['tr',12,3,5], comment='translation equipement') # Comment to insert before the transfo card
        """

        # We substitute the trcl cards with their value
        dictElem = tk.SetCstTrcl(self._dictElem)

        # We apply the transfo
        self._dictElem = tk.ApplyTransfo(dictElem, lsInput, comment)

        # Conversion to scalar unit
        lsInputScal = tk.ConvertTr(lsInput)
        if len(lsInput) <= 4:
            lsInputScal = lsInputScal + [1,0,0, 0,1,0, 0,0,1, 1]

        # Transfo of the object
        lsObjetTr = self.GetTr()

        # Same calculations as ApplyTransfo but applied to the object transfo
        # Calcul matrice de rotation
        npMatInputTr = np.array(lsInputScal[4:13]).reshape(3,3)
        npMatTr0 = np.array(lsObjetTr[4:13]).reshape(3,3)
        if lsObjetTr[13] == 1:
            npMatTrNew = npMatTr0.dot(npMatInputTr)
        elif lsObjetTr[13] == -1:
            npMatTrNew = npMatTr0.dot(npMatInputTr)
            npMatTrNew = npMatTrNew.transpose() # pas sur, a verifier

        # Addition of the translation part
        tdTranslat = (npMatInputTr.transpose()).dot(np.array(lsObjetTr[1:4]).transpose()) \
                        + np.array(lsInputScal[1:4])

        # Update of the object transfo
        for i in range(1,4):
            self._Trans[i] = tdTranslat[i-1]
        npTemp = npMatTrNew.reshape(9,1)
        for i in range(4,13):
            self._Trans[i] = npTemp[i-4][0]

        # Update of the list of transfo operations
        if len(comment) == 0:
            comment = f"Generalised transform: {lsInput}"
        self._FctTrans.append(comment)

    def GetTr(self):
        """
        GetTr():

        Returns the transformations applied to the object.

        Can be directly used by Transform:
        obj.Transform(obj2.GetTr())
        """

        return self._Trans

    def FindTrCard(self,iTr):
        """
        FindTrCard(iTr):

        Returns the transformation iTr of the object as a dictionnary with keys:
        res["num"]       : transform number
        res["unit"]      : unit ('deg' or 'scal')
        res["strtr"]     : card ('*tr' or 'tr')
        res["translat"]  : list of length 3 of the translation vector
        res["rot"]       : list of length 9 of the rotation matrix
        res["sens"]      : last parameter of the card (1 or -1)
        res["tr"] = [res["strtr"]] + res["translat"] + res["rot"] + [res["sens"]]
                         : can be used as an entry for function Transform

        Returns empty dictionnary if no card is found.

        Examples:
        dTr = obj.FindTrCard(5) # Find card 'tr5' and stores it in dTr.
        """

        # Init
        res = dict()

        # If the transfo is in the file, we continue
        for i in self._dictElem["trans"]:
            lsLine = self._dictElem["fich"][i]
            if iTr == tk.GetCardNumber(lsLine[0]):
                # Card found, we read it
                res = tk.ReadTrCard(lsLine)
                break

        return res

    def Renum(self,cell = 1, surf = 1, trans = 1):
        """
        Renum(cell = 1, surf = 1, trans = 1):

        Function for renumbering an object (cells, surfaces and transformations),
        by default from 1.

        Example:
        obj.Renum()
        obj.Renum(cell = 100) # renumber cells from 100
        """

        dictOut = tk.Renum(self._dictElem, [-1], cell, [-1], surf, trans)
        self._dictElem = deepcopy(tk.LectElem(dictOut["fich"]))

        return

    def Extract(self,tiListeInputCell, mode = 'extract', radius = 2000):
        """
        Extract(tiListeInputCell, mode = 'extract', radius = 2000):

        Function to extract a list of cells (and necessary surfaces, material
        and transformation) from an object.
        By default, a bounding cell of radius 20m is added to visualize the
        file with mcnp.
        This function can be used to then make an insertion by cell with
        'InsertCells', the insertion by bounding surface not working in the
        general case.

        Warning: mat not work on lattices due to dependance issues between
        between universes and fill cells (work in progress).

        Parametres:
        mode     : 'extract' (default) extracts cells in 'tiListeInputCell'.
                   'subtract' allows to extract the complement of the list of
                   cells given (ignores the last two cells, i.e., the gas cell
                   and graveyard cell).
        radius   : radius of the bounding sphere in cm.

        Example:
        new_obj = objet.Extract([3, 4, 5])
        new_obj = objet.Extract([3, 4, 5], radius = 10e2) # set bounding shere radius to 10m
        new_obj = objet.Extract(range(3,1000))
        new_obj = objet.Extract([3, 4, 5],mode='subtract')
        """

        # Verification
        if mode != 'extract' and mode != 'subtract':
            print(f"Extract: Error, unknown input 'mode' ({mode} ?), default mode chosen.")
            mode = 'extract'

        # Construction of the list of cells
        tiListeCellNew = list()
        if mode == 'extract':
            # The cells remain unchanged
            tiListeCellNew = deepcopy(tiListeInputCell)
        else:
            # We construct the list of complementary cells (except the last two)
            for iCell in self._dictElem["cell"][:-2]:
                iNum = tk.GetCellNum(self._dictElem["fich"][iCell][0])
                if iNum not in tiListeInputCell:
                    tiListeCellNew.append(iNum)

        # Extraction of the cells of interest
        lsLignes = deepcopy(self._dictElem["fich"])
        dictGroupes = deepcopy(self._dictElem["groups"])
        dictNew = tk.Extract(lsLignes, tiListeCellNew, radius, dictGroupes = dictGroupes)

        # Creation of the new object
        NewElem = object.__new__(go)

        # Assignation du dico
        NewElem._dictElem = deepcopy(dictNew)

        # Autre attribut
        NewElem.geom = 'Extract of cells ' + str(tiListeCellNew) + ' from ' + self.geom
        NewElem._InGeom = list()
        NewElem._Trans = self.GetTr()
        NewElem._tiNumTally = dict()
        for s in MCNP_FIRST_TALLY.keys():
            self._tiNumTally[s] = list()
        NewElem._tiTrTally = list()
        NewElem._FctTrans = list()

        return NewElem

    def _InsertMat(self,dictNew,geom):
        """
        Function for merging the materials of two files.
        Modifies dictNew.
        """

        # Obtention de la liste des numeros de materiaux PN et leur position

        lsKeyMatPN = ["matpn","matmxp","matmxh","matmxn","matmt"]
        lsKeyMat = ["mat"] + lsKeyMatPN

        dict_tiMatNumberSelf = dict()
        dict_lsMatFichSelf = dict()
        dict_lsMatCommentSelf = dict()
        dict_tiMatIndexSelf = dict()
        for sKey in lsKeyMat:
            dict_tiMatNumberSelf[sKey] = list()
            dict_lsMatFichSelf[sKey] = list()
            dict_lsMatCommentSelf[sKey] = list()
            dict_tiMatIndexSelf[sKey] = list()
            iCount = 0
            for iMat in self._dictElem[sKey]:

                # Rangement du numero du matériau
                sLine = self._dictElem["fich"][iMat][0]
                iNumMat = tk.GetCardNumber(sLine)
                dict_tiMatNumberSelf[sKey].append(iNumMat)

                #
                dict_tiMatIndexSelf[sKey].append(iCount)
                iCount = iCount + 1

                # Insertion des commentaires precedent la carte
                dict_lsMatCommentSelf[sKey].append(tk.GatherTopComments(self._dictElem["fich"],iMat))

                # Ajout de la carte materiau
                dict_lsMatFichSelf[sKey].append(self._dictElem["fich"][iMat])

        # Pareil pour les cartes du nouvel element
        dict_tiMatNumberNew = dict()
        dict_lsMatFichNew = dict()
        dict_lsMatCommentNew = dict()
        dict_tiMatIndexNew = dict()
        for sKey in lsKeyMat:
            dict_tiMatNumberNew[sKey] = list()
            dict_lsMatFichNew[sKey] = list()
            dict_lsMatCommentNew[sKey] = list()
            dict_tiMatIndexNew[sKey] = list()
            iCount = 0
            for iMat in dictNew[sKey]:

                # Rangement du numero du matériau
                sLine = dictNew["fich"][iMat][0]
                iNumMat = tk.GetCardNumber(sLine)
                dict_tiMatNumberNew[sKey].append(iNumMat)

                #
                dict_tiMatIndexNew[sKey].append(iCount)
                iCount = iCount + 1

                # Insertion des commentaires precedent la carte
                dict_lsMatCommentNew[sKey].append(tk.GatherTopComments(dictNew["fich"],iMat))

                # Ajout de la carte materiau
                dict_lsMatFichNew[sKey].append(dictNew["fich"][iMat])

        # Liste des matériaux à insérer
        lsMatInsert = list()

        # On parcours les materiaux par numéro
        tiMatNumberFind = list()
        for iNew,iMatNumber in enumerate(dict_tiMatNumberNew["mat"]):

            # Comparaison a la liste des materiaux de l'objet acceuillant
            iFlagMatInsert = 1
            for iSelf,iMatNumberSelf in enumerate(dict_tiMatNumberSelf["mat"]):

                # Parcours des cartes m, mpn, mx et mt
                iFlagMatDiff = 0
                for sKey in lsKeyMat:

                    # Carte new corespondante
                    if iMatNumber in dict_tiMatNumberNew[sKey]:
                        iNewKey = dict_tiMatIndexNew[sKey][dict_tiMatNumberNew[sKey].index(iMatNumber)]
                        lsMatNew = dict_lsMatFichNew[sKey][iNewKey]
                    else:
                        lsMatNew = list()

                    # Carte self corespondante
                    if iMatNumberSelf in dict_tiMatNumberSelf[sKey]:
                        iSelfKey = dict_tiMatIndexSelf[sKey][dict_tiMatNumberSelf[sKey].index(iMatNumberSelf)]
                        lsMatSelf = dict_lsMatFichSelf[sKey][iSelfKey]
                    else:
                        lsMatSelf = list()

                    # On verifie d'abord la taille
                    if len(lsMatSelf) == len(lsMatNew):
                        iLenCarte = len(lsMatSelf)

                        # Comparaison ligne par ligne
                        for iLine in range(iLenCarte):
                            sLineNew = lsMatNew[iLine] + ' ' # Rajout d'un espace pour prendre en compte si pas de $
                            sLineNew = sLineNew.replace('\t',' ')
                            lsLineNew = sLineNew[:sLineNew.find('$')].split()
                            sLineSelf = lsMatSelf[iLine] + ' ' # Rajout d'un espace pour prendre en compte si pas de $
                            sLineSelf = sLineSelf.replace('\t',' ')
                            lsLineSelf = sLineSelf[:sLineSelf.find('$')].split()

                            # Il faut ignorer la carte pour la premiere ligne
                            if iLine == 0:
                                lsLineNew = lsLineNew[1:]
                                lsLineSelf = lsLineSelf[1:]

                            if lsLineNew != lsLineSelf:
                                # Materiaux non identiques
                                iFlagMatDiff = 1
                                break

                    else:
                        # Materiaux non identiques
                        iFlagMatDiff = 1

                # Test si materiau identique trouve
                if iFlagMatDiff == 0:
                    iFlagMatInsert = 0

                    # Numero de materiau de l'acceuillant
                    iMatNumber0 = iMatNumberSelf
                    break

            # On insere le materiau et/ou on change le numero selon le cas
            if iFlagMatInsert == 0:
                # Swap le numero ici
                if iMatNumber != iMatNumber0:

                    # On echange iMatNumber par iMatNumber0 (interversion si iMatNumber0 existe dans dictNew)
                    tk.SwapMatNumber(dictNew,iMatNumber0,iMatNumber)

                    # Mise a jour necessaire ?


            else: # iFlagMatInsert == 1
                # On choisi un numero et on insere le nouveau materiau
                if iMatNumber not in dict_tiMatNumberSelf["mat"]:
                    iMatNumberNew = iMatNumber
                else:
                    iFlagStop = 0
                    iMatNumberNew = iMatNumber
                    while iFlagStop == 0:
                        iMatNumberNew = iMatNumberNew + 1

                        # Si le nouveau numero n'est ni dans lles listes initiales
                        # de self ou de new, alors a priori aucun risque
                        if (iMatNumberNew not in dict_tiMatNumberSelf["mat"]) \
                            and (iMatNumberNew not in dict_tiMatNumberNew["mat"])\
                            and iMatNumberNew not in tiMatNumberFind:

                            iFlagStop = 1

                    # On change le numero
                    tk.SwapMatNumber(dictNew,iMatNumberNew,iMatNumber)

                # Mise a jour de la liste des matériaux trouvés
                tiMatNumberFind.append(iMatNumberNew)

                # Insertion de la carte materiau
                for sKey in lsKeyMat:

                    # Carte new corespondante
                    if iMatNumber in dict_tiMatNumberNew[sKey]:
                        iNewKey = dict_tiMatIndexNew[sKey][dict_tiMatNumberNew[sKey].index(iMatNumber)]
                        lsMatNew = dict_lsMatFichNew[sKey][iNewKey]
                        lsMatCommentNew = dict_lsMatCommentNew[sKey][iNewKey]

                        # Retrieve card and particle type
                        sCard, sCardPart = tk.GetCardType(lsMatNew[0])
                        if len(sCardPart) > 0:
                            sCardPart = ':' + sCardPart

                        # Swap numbers
                        lsMatNew[0] = sCard + str(iMatNumberNew)\
                            + sCardPart + lsMatNew[0][lsMatNew[0].find(' '):]

                        # Insertion
                        lsMatInsert.extend(lsMatCommentNew)
                        lsMatInsert.extend(lsMatNew)

        # Liste des matériaux
        lsMatFichSelf = tk.ConcatCard(self._dictElem,"matall")
        if len(lsMatInsert) > 0:
            # Insertion de commentaires
            lsMatFichSelf.append(['c '])
            lsMatFichSelf.append(['c ' + '='*78])
            lsMatFichSelf.append(['c New material cards from:'])
            lsMatFichSelf.append(['c ' + geom])
            lsMatFichSelf.append(['c ' + '='*78])

            # Ajout de la carte materiau
            lsMatFichSelf.extend(lsMatInsert)
        else:
            # Insertion de commentaires
            lsMatFichSelf.append(['c '])
            lsMatFichSelf.append(['c ' + '='*78])
            lsMatFichSelf.append(['c Zero new material cards from:'])
            lsMatFichSelf.append(['c ' + geom])
            lsMatFichSelf.append(['c ' + '='*78])

        return lsMatFichSelf#, dictNew

    def WriteMCNPFile(self,fichier, imp='in'):
        """
        WriteMCNPFile(filename, imp='in'):

        Writes the object in MCNP format.
        A formatting of the file is performed beforehand.

        Parametre :
            imp     : if imp='in' then the 'imp' cards are left on the
                      cell lines,
                      if imp='out', the 'imp' cards are relegated to the card block.

        Example:
        obj.WriteMCNPFile('myfile')
        """

        # Copie locale
        dictElemIn = deepcopy(self._dictElem)

        # On remplace les trcl constantes par un numero de transfo
        dictElem = tk.SwapCstTrclByNum(dictElemIn, addtr = self._tiTrTally) # Attention la categorie MCNP est detruite par LectElem

        # Mise en forme
        dictElem = tk.FormatImpOut(dictElem, imp=imp)

        # Insertion des blocs MCNP si présents
        if "mcnp" in dictElemIn.keys():
            dictElem["fich"].insert(dictElem["saut"][2],dictElemIn["mcnp"])

        # Insertion des infos fichiers
        sInfo = 'c ' + self.__str__()
        dictElem["fich"].insert(0,[sInfo.replace('\n','\nc ')])

        # Ecriture
        with open(fichier,'w') as File:
            for i in dictElem["fich"]:
                for s in i:
                    File.write(s + '\n')

    def ResolveTRCL(self):
        """
        ResolveTRCL():

        Function for re-numbering surfaces and cells related to the 'trcl'
        cards that poses problem if surfaces numbers are >= 1000 or if generated
        surfaces numbers already exist.

        If one call to the function is not enough, you may call it several times.

        Note: MCNP manual states that cell numbers with trcl cards should not be
        >= 1000, but in practice, that does not seem to be a problem. It also
        states that surface numbers with tr cards should not be >= 1000, but
        again, this does not seem to be a problem.

        Example:
        obj.ResolveTRCL()
        """

        # Init
        iOK = 0
        bOK_1 = False
        bOK_2 = False
        dictElemBoucle = deepcopy(self._dictElem)

        # Boucles successives to cover all cases
        for iDict in range(10):
            # Init
            tiCellRenumUnique = list()
            tiCellRenum = list()
            tiSurfRenum = list()
            tiCellInLine = list()
            tiLNCellTrcl = list()

            # On parcourt les cellules
            tiCell = deepcopy(dictElemBoucle["cell"])
            for iLigne in tiCell:

                # Interpretation de la ligne
                dictCell = tk.GatherCellGeo(dictElemBoucle["fich"][iLigne])

                # For trcl cards
                if "trcl" in ' '.join(dictCell["strfin"]).lower():
                    tiLNCellTrcl.append(iLigne)

                    # On collecte la cellule si >= 1000
                    # This is according to MCNP manual but does not seem to be
                    # necessary
                    iCellNum = dictCell["num"][0]
                    if iCellNum >= 1000 and iCellNum not in tiCellRenum:
                        tiCellRenum.append(iCellNum)

                    # On collecte les surfaces >= 1000
                    for i in dictCell["surf"]:
                        iSurf = abs(int(i))
                        if iSurf >= 1000 and iSurf not in tiSurfRenum:
                            tiSurfRenum.append(abs(int(i)))

                    # On memorise les cellules concernees par les likes
                    # if "like" in sSubLineSum.lower():
                    #     tiCellLikeLine.extend(dictCell["cell"])
                    tiCellInLine.extend(dictCell["cell"])


            # Traitements des likes
            if len(tiCellInLine) > 0:
                for iLigne in tiCell:

                    # Numero de cellule
                    iCellNum = tk.GetCellNum(dictElemBoucle["fich"][iLigne][0])

                    if iCellNum in tiCellInLine:
                        # Interpretation de la ligne
                        dictCell = tk.GatherCellGeo(dictElemBoucle["fich"][iLigne])

                        # On collecte les surfaces > 1000
                        for i in dictCell["surf"]:
                            iSurf = abs(int(i))
                            if iSurf >= 1000 and iSurf not in tiSurfRenum:
                                tiSurfRenum.append(abs(int(i)))

            # Renumerotation des surfaces
            if len(tiCellRenum) > 0 or len(tiSurfRenum) > 0:

                # Re-numbering
                dictOut = tk.Renum(dictElemBoucle,\
                                   tiCellRenum, 1,\
                                   tiSurfRenum, 1,\
                                       -1)

                dictElemBoucle = deepcopy(tk.LectElem(dictOut["fich"]))
            else:
                bOK_1 = True


            # Now checking if there are conflicts with generated surfaces and
            # cells

            # Liste des surfaces
            tiFoundSurf = list()
            for iLigne in dictElemBoucle["surf"]:
                tiFoundSurf.append(tk.GetLineNum(dictElemBoucle["fich"][iLigne][0]))

            # List of surfaces within cells
            lSurfInCells = list()
            tiSurfInCellsIndex = list()
            for iLigne in dictElemBoucle["cell"]:
                # Interpretation de la ligne
                dictCell = tk.GatherCellGeo(dictElemBoucle["fich"][iLigne])

                tiSurfInCellsIndex.append(dictCell["num"][0])
                lSurfInCells.append([abs(int(i)) for i in dictCell["surf"]])

            # Check de l'unicité des surfaces
            for iLigne in tiLNCellTrcl:

                # Interpretation de la ligne
                dictCell = tk.GatherCellGeo(dictElemBoucle["fich"][iLigne])

                # Surface en plus de la cellule
                tiSurfMore = list()
                for i in dictCell["cell"]:
                    tiSurfMore.extend(lSurfInCells[tiSurfInCellsIndex.index(i)])

                # Parcours des surfaces de la cellule
                for i in dictCell["surf"] + tiSurfMore:
                    iS = abs(int(i))
                    iC = dictCell["num"][0]
                    iSGen = iS + 1000*iC
                    if iSGen in tiFoundSurf:
                        # Problem, generated surface already exists
                        tiCellRenumUnique.append(iC)

            # Renumerotation
            if len(tiCellRenumUnique) > 0:
                # We choose to renumber from this
                iCellStart = min(tiCellRenumUnique)+1

                # Re-numbering
                dictOut = tk.Renum(dictElemBoucle,\
                                   tiCellRenumUnique, iCellStart,\
                                       [], 1, -1) # don't renumber surfaces

                dictElemBoucle = deepcopy(tk.LectElem(dictOut["fich"]))
            else:
                bOK_2 = True

            # Check if a solution has been found
            if bOK_1 and bOK_2:
                self._dictElem = deepcopy(dictElemBoucle)
                iOK = 1
                break


        # Si pas de solution
        if iOK == 0:
            print("ResolveTRCL: No solution found after 10 tries. Try to run ResolveTRCL multiple times.")

        return



    def Translat(self, trans, comment=''):
        """
        Translat(trans, comment=''):

        Function to make a translation.

        Example:
        obj.Translat([10,23,0]) # 10cm along axis X, 23cm along axis Y
        obj.Translat([10,23,0], comment='positionning the detector')
        """

        # Commentaire
        if len(comment) == 0:
            comment = 'Translation: ' + str(trans)

        # Transformee
        self.Transform(['tr'] + trans, comment)


    def TrRotX(self, trans=[0,0,0], angle=0, unit='deg', comment=''):
        """
        TrRotX(trans=[0,0,0], angle=0, unit='deg', comment=''):

        Function to make a translation and a rotation around X ("from Y to Z").
        By default, the rotations are in degrees.

        Example:
        obj.TrRotX(angle=30) # Rotation only
        obj.TrRotX(angle=1.2, unit='rad') # Rotation only in radian
        obj.TrRotX(trans=[140,25,30], angle=30) # Translation and rotation
        obj.TrRotX(angle=1.2, unit='rad', comment='positionning the detector') # Adding a comment
        """

        # Commentaire
        if len(comment) == 0:
            if angle == 0:
                comment = 'Translation: ' + str(trans)
            elif trans == [0,0,0]:
                comment = 'Rotation X: ' + str(angle)
            else:
                comment = 'Translation: ' + str(trans) + ' Rotation X: ' + str(angle)

        # Unite
        if unit == 'deg':
            anglerad = math.radians(angle)
        elif unit == 'rad':
            anglerad = angle
        else:
            print(f"TrRotX: unknown unit (unit = {unit} ?).")
            sys.exit()

        # Anciens vecteurs
        X = np.array([1,0,0])
        Y = np.array([0,1,0])
        Z = np.array([0,0,1])

        # Nouveaux vecteurs
        Xp = np.array([1, 0, 0])
        Yp = np.array([0, math.cos(anglerad), math.sin(anglerad)])
        Zp = np.array([0, math.cos(math.pi*0.5 + anglerad), math.sin(math.pi*0.5 + anglerad)])

        # Matrice de rotation
        tdVecRot = [X.dot(Xp), Y.dot(Xp), Z.dot(Xp), X.dot(Yp), Y.dot(Yp), Z.dot(Yp), X.dot(Zp), Y.dot(Zp), Z.dot(Zp)]

        # Transformee
        self.Transform(['tr'] + trans + tdVecRot, comment)


    def TrRotY(self, trans=[0,0,0], angle=0, unit='deg', comment=''):
        """
        TrRotY(trans=[0,0,0], angle=0, unit='deg', comment=''):

        Function to make a translation and a rotation around Y ("from Z to X").
        By default, the rotations are in degrees.

        Example:
        obj.TrRotY(angle=30) # Rotation only
        obj.TrRotY(angle=1.2, unit='rad') # Rotation only in radian
        obj.TrRotY(trans=[140,25,30], angle=30) # Translation and rotation
        obj.TrRotY(angle=1.2, unit='rad', comment='positionning the detector') # Adding a comment
        """

        # Commentaire
        if len(comment) == 0:
            if angle == 0:
                comment = 'Translation: ' + str(trans)
            elif trans == [0,0,0]:
                comment = 'Rotation Y: ' + str(angle)
            else:
                comment = 'Translation: ' + str(trans) + ' Rotation Y: ' + str(angle)

        # Unite
        if unit == 'deg':
            anglerad = math.radians(angle)
        elif unit == 'rad':
            anglerad = angle
        else:
            print(f"TrRotY: unknown unit (unit = {unit} ?).")
            sys.exit()

        # Anciens vecteurs
        X = np.array([1,0,0])
        Y = np.array([0,1,0])
        Z = np.array([0,0,1])

        # Nouveaux vecteurs
        anglerad = -anglerad
        Xp = np.array([math.cos(anglerad), 0, math.sin(anglerad)])
        Yp = np.array([0, 1, 0])
        Zp = np.array([math.cos(math.pi*0.5 + anglerad), 0, math.sin(math.pi*0.5 + anglerad)])

        # Matrice de rotation
        tdVecRot = [X.dot(Xp), Y.dot(Xp), Z.dot(Xp), X.dot(Yp), Y.dot(Yp), Z.dot(Yp), X.dot(Zp), Y.dot(Zp), Z.dot(Zp)]

        # Transformee
        self.Transform(['tr'] + trans + tdVecRot, comment)


    def TrRotZ(self, trans=[0,0,0], angle=0, unit='deg', comment=''):
        """
        TrRotZ(trans=[0,0,0], angle=0, unit='deg', comment=''):

        Function to make a translation and a rotation around Z ("from X to Y").
        By default, the rotations are in degrees.

        Example:
        obj.TrRotZ(angle=30) # Rotation only
        obj.TrRotZ(angle=1.2, unit='rad') # Rotation only in radian
        obj.TrRotZ(trans=[140,25,30], angle=30) # Translation and rotation
        obj.TrRotZ(angle=1.2, unit='rad', comment='positionning the detector') # Adding a comment
        """

        # Commentaire
        if len(comment) == 0:
            if angle == 0:
                comment = 'Translation: ' + str(trans)
            elif trans == [0,0,0]:
                comment = 'Rotation Z: ' + str(angle)
            else:
                comment = 'Translation: ' + str(trans) + ' Rotation Z: ' + str(angle)

        # Unite
        if unit == 'deg':
            anglerad = math.radians(angle)
        elif unit == 'rad':
            anglerad = angle
        else:
            print(f"TrRotZ: unknown unit (unit = {unit} ?).")
            sys.exit()

        # Anciens vecteurs
        X = np.array([1,0,0])
        Y = np.array([0,1,0])
        Z = np.array([0,0,1])

        # Nouveaux vecteurs
        Xp = np.array([math.cos(anglerad), math.sin(anglerad), 0])
        Yp = np.array([math.cos(math.pi*0.5 + anglerad), math.sin(math.pi*0.5 + anglerad), 0])
        Zp = np.array([0, 0, 1])

        # Matrice de rotation
        tdVecRot = [X.dot(Xp), Y.dot(Xp), Z.dot(Xp), X.dot(Yp), Y.dot(Yp), Z.dot(Yp), X.dot(Zp), Y.dot(Zp), Z.dot(Zp)]

        # Transformee
        self.Transform(['tr'] + trans + tdVecRot, comment)


    def TrEuler(self, trans=[0,0,0], a=0, b=0, g=0, unit='deg', comment=''):
        """
        TrEuler(trans=[0,0,0], a=0, b=0, g=0, unit='deg', comment=''):

        Performs a transformation with the Euler angles alpha, beta and gamma,
        respectively of precession, nutation and proper rotation around axes Z,
        X' and Z''.
        The angles are in degrees by default.
        See the documentation for a clear explanation of the meaning of the angles.

        Parametres:
        trans    [cm]    =[0,0,0]    : Vector of translation to apply.
        a       [deg]    =0          : Precession angle around Z.
        b       [deg]    =0          : Nutation angle around X'.
        g       [deg]    =0          : Rotation angle around Z''.
        unit    [string]='deg'       : Unit in which the angles are expressed. Set unit='rad' for radians.
        comment [string]=''          : Comment

        Example:
        obj.TrEuler(a=5,b=6.2) # Rotation only
        obj.TrEuler(a=5,g=10,trans=[0,5,0]) # Rotation and translation
        obj.TrEuler(a=0.1,trans=[0,5,0],unit='rad') # Rotation in radian and translation
        obj.TrEuler(a=5,g=10,trans=[0,5,0],comment='Rotation of the detector') # Adding a comment
        """

        # Commentaire
        if len(comment) == 0:
            if trans == [0,0,0]:
                comment = "Rotation of Euler angles: " + str([a,b,g]) + ' ' + unit
            else:
                comment = "Translation: " + str(trans) + "   Rotation of Euler angles: " + str([a,b,g]) + ' ' + unit

        # Calcul de la matrice
        tdMat = tk.EulerZXZ( a=a, b=b, g=g, unit=unit)

        # Transformee
        self.Transform(['tr'] + trans + tdMat, comment)


    def TrRotU(self,u=[1,0,0],trans=[0,0,0],angle=0,unit='deg', comment=''):
        """
        TrRotU(u=[1,0,0], trans=[0,0,0], angle=0, unit='deg', comment=''):

        Performs a rotation of an angle around the axis u.
        Vector 'u' does not need to be normalized.

        Parametres :
        u        : Vector of the rotation axis
        trans    : Vector of translation to apply
        angle    : Angle of the rotation
        unit    : Unit in which the angle is expressed. Set unit='rad' for radians.
        comment : Comment

        Example:
        obj.TrRotU(u=[-1,1,0],angle=7) # Rotation of 7 deg

        """

        # Commentaire
        if len(comment) == 0:
            if trans == [0,0,0]:
                comment = "Rotation of angle: " + str(angle) + ' ' + unit + " around axis " + str(u)
            else:
                comment = "Translation: " + str(trans) + "   Rotation of angle: " + str(angle) + ' ' + unit + " around axis " + str(u)


        # Calcul de la matrice
        tdMat = tk.RotU(u=u,angle=angle,unit=unit)

        # Transformee
        self.Transform(['tr'] + trans + tdMat, comment)

        return





    def SwapCellMat(self, num_cell, mat=0, dens=0):
        """
        SwapCellMat(num_cell, mat=0, dens=0):

        Function for replacing the material of a cell by the one indicated by "mat"
        with the density "dens".

        If mat = -1, then only the density is changed while keeping the same material.

        Example:
            obj.SwapCellMat(95) # the cell 95 will be made of void
            obj.SwapCellMat([100,135,300])
            obj.SwapCellMat([100,135,300],mat=0) # cells replaced by void
            obj.SwapCellMat([100,135,300],mat=-1,dens=2.5) # changing the densities to 2.5g/cm3

        Remark:
            Does not work on cells of type "like ... but"
        """

        # Verification
        if type(num_cell) is int:
            num_cell = [num_cell]
        elif type(num_cell) is range:
            num_cell = list(num_cell)

        # If materiau vide
        if mat == 0 or dens == 0:
            mat = 0
            dens = 0
        elif mat > 0 :
            # On commence par rassembler la liste des cartes materiaux de l'objet
            liMat = list()
            for i in self._dictElem["mat"]:
                liMat.append(tk.GetLineNum(self._dictElem["fich"][i][0]))

            # Verification
            if mat not in liMat:
                print("SwapCellMat: Error, material card does not belong to the object: " + self.geom)
                return

        # On cherche la cellule en question
        iOK = 0
        for i in self._dictElem["cell"]:
            # Ligne courante
            sLigne = self._dictElem["fich"][i][0]

            # Numero de la cellule
            iCell = tk.GetCellNum(sLigne)
            if iCell in num_cell:
                iOK = 1

                # Information sur la cellule
                dictCell = tk.GetCellGeo(sLigne)

                # Si dictCell["mat"][0] == -1 alors la cellule est un like ... but
                if dictCell["mat"][0] >= 0:

                    # Si vide
                    if mat == 0:
                        sMat = ' 0 '
                    elif mat == -1:
                        sMat = ' ' + str(dictCell["mat"][0]) + ' -' + str(abs(dens)) + ' '
                    else:
                        sMat = ' ' + str(mat) + ' -' + str(abs(dens)) + ' '

                    # Reconstruction en changeant le materiau
                    self._dictElem["fich"][i][0] = str(dictCell["num"]) + sMat \
                     + dictCell["strgeo"] + ' ' + dictCell["strfin"] + ' ' + dictCell["strcom"]


        if iOK == 0:
            print("SwapCellMat: Error, none of the cells are part of the object: " + self.geom)
            return

        return


    def _CheckMCNPTallyNumber(self,ntal,tallytype,warning = 'on'):
        """
        _CheckMCNPTallyNumber(ntal,tallytype,warning = 'on'):

        Function for checking the availability of a tally number for MCNP.

        Parametres :
            ntal      : tally number requested
            tallytype : type of the tally ("F1", "F5", etc ...)

        Example:
        newtalynumber = obj._CheckMCNPTallyNumber(5,"F5")
        """

        # Verification type de tally
        if tallytype not in self._tiNumTally.keys():
            print(f"Error: tally type (tallytype = {tallytype}) does not exist.")
            sys.exit()

        # Digit par lequel doit finir le tally
        iResteTally = MCNP_FIRST_TALLY[tallytype]%10

        # Increment du numero du tally
        if ntal == -1:
            if len(self._tiNumTally[tallytype]) == 0:
                # Si premier tally alors on initialise
                ntal = MCNP_FIRST_TALLY[tallytype]
            else:
                # Increment numero tally
                ntal = self._tiNumTally[tallytype][-1] + 10
            self._tiNumTally[tallytype].append(ntal)
        else:
            # Verification
            if ntal%10 != iResteTally:
                print("Error, ntal=" + str(ntal) + " must end by " + str(iResteTally) + ".")
                sys.exit()

            if len(self._tiNumTally[tallytype]) == 0:
                # Si premier tally alors on initialise
                self._tiNumTally[tallytype].append(ntal)

            # On regarde si le numero de tally demande est deja utilise
            elif ntal in self._tiNumTally[tallytype]:
                if warning == 'on':
                    print("Error, ntal=" + str(ntal) + " is already in use. We pick an other.")
                ntal = ntal + 10
                while ntal in self._tiNumTally[tallytype]:
                    ntal = ntal + 10
                self._tiNumTally[tallytype].append(ntal)
                if warning == 'on':
                    print("We choose ntal=" + str(ntal))

        return ntal


    def AddMCNPCard(self,lsCard):
        """
        AddMCNPCard(lsCard):

        Function for adding the content of the input list to the card block
        of the MCNP file.

        Parametres :
            lsCard            : string or list of strings to be added.


        Example :
        obj.AddMCNPCard("c ") # Add a coment line
        obj.AddMCNPCard(["c tally","F4:P 5","FM4 -1 -5 -6"]) # Add a tally

        """

        # Verification sur le type
        lsFile = list()
        if type(lsCard) is str:
            lsFile.append(lsCard)

        elif type(lsCard) is list:
            for i,s in enumerate(lsCard):
                if type(s) is str:
                    lsFile.append(s)
                else:
                    print(f"AddMCNPCard: Error, input must be a list of strings (input n°{i} : {s} ?)." )
                    print("Exit.")
                    sys.exit()
        else:
            print(f"AddMCNPCard: Error, input must be a string or a list of strings({lsCard} ?)." )
            print("Exit.")
            sys.exit()

        # Remplissage de la categorie
        if "mcnp" not in self._dictElem.keys():
            self._dictElem["mcnp"] = lsFile
        else:
            self._dictElem["mcnp"].extend(lsFile)

        return

    def AddMCNPCardFromFile(self,sFile):
        """
        AddMCNPCardFromFile(sFile):

        Function for adding the content of the input file to the card block
        of the MCNP file.

        Parametres :
            sFile            : path to the file


        Example:
        obj.AddMCNPCardFromFile("./DATA/source_definition.txt") # Adding a source to my file

        """

        # Lecture du fichier
        with open(sFile,'r',errors='ignore') as fid:
            lsFile = fid.read().splitlines()

        # Remplissage de la categorie
        if "mcnp" not in self._dictElem.keys():
            self._dictElem["mcnp"] = lsFile
        else:
            self._dictElem["mcnp"].extend(lsFile)

        return


    def AddMCNPTally(self, tally = "F4:P", comment = "", group = "", card = [""]):
        """
        AddMCNPTally(tally = "F4:P", comment = "", group = "", card = [""])

        Function for adding tallies (except type 5 and mesh) from a list
        of surfaces or cells of the group "group".

        About tally number :
            - The number of the tally in the card "tally" is only present
              to determine the type of tally, i.e., "F4:P" or "F14:P" gives the
              same result.
            - The number of the tally in card is ignored, card = ["FM -1 -5 -6"] is
              a valid input.

        Parametres :
            tally            : tally card (ex: "+F6", "F4:P", "+*F8:N")
            comment            : comment line to insert before the tally
            group            : name of the group containing the tally information
            card            : list of tally data cards to add (ex: ["FM4 -1 -5 -6","FS4 -12 -32"])
        """

        # Type de carte
        sTallyUnit = ""
        sTallyPart = ""
        sTallyNumber = ""
        if ":" in tally:
            sTallyPart = ":" + tally.split(':')[1]
        for s in tally.split(':')[0]:
            if s.isdigit():
                sTallyNumber = sTallyNumber + s
            else:
                sTallyUnit = sTallyUnit + s
        ntal = int(sTallyNumber)

        # Verification si aucun numero de tally
        if len(sTallyNumber) == 0:
            print("AddMCNPTally: Error, tally number must be specified in 'tally'.")
            print("Exit.")
            sys.exit()

        # Type de carte
        lsCard = list()
        if len(card) > 0 and len(card[0].strip()) > 0:
            for sCartInput in card:
                sCard = ""
                sCardNumber = ""
                for s in sCartInput.split()[0]:
                    # On recupere la description de la carte sauf le numéro de tally
                    if s.isdigit() is False:
                        sCard = sCard + s
                    else:
                        sCardNumber = sCardNumber + s
                lsCard.append(sCard)

                # Verification
                if len(sCardNumber) > 0 and sTallyNumber[-1] != sCardNumber[-1]:
                    print("AddMCNPTally: Warning, cards 'tally' and 'card' do not possess the same tally type.")
                    print("Only input 'tally' matters for tally type.")

        # Cellule ou surface
        if sTallyNumber.endswith("5"):
            print("AddMCNPTally: Error, tally 5 not handled by this function. Use AddMCNPPointTally.")
            print("Exit.")
            sys.exit()
        if sTallyNumber.endswith(("1","2")):
            subgroup = "surf"
        elif sTallyNumber.endswith(("4","6","7","8")):
            subgroup = "cell"
        elif sTallyNumber.endswith("3"):
            print("AddMCNPTally: Error, tally 3 (TMESH) not handled by this function.")
            print("Exit.")
            sys.exit()
        else:
            print(f"AddMCNPTally: Error, unknown tally type ({tally} ?).")
            print("Exit.")
            sys.exit()

        # Construction du tally
        lsFile = list()
        if len(comment) > 0:
            lsFile.append("c " + comment)

        # Check group
        if self.CheckGroup(group,subgroup):

            # Liste des cellules ou surfaces de ce groupe
            tdTallyStuff = self.GetGroup(group,subgroup)

            # Insertion du tally
            for i in range(len(tdTallyStuff)):

                # Increment du numero du tally
                ntal = self._CheckMCNPTallyNumber(ntal,"F" + sTallyNumber[-1],warning='off')

                # Construction du tally
                lsFile.append(f"{sTallyUnit}{ntal}{sTallyPart} {tdTallyStuff[i]}")

                # Ajout de la carte
                if len(card) > 0 and len(card[0].strip()) > 0:
                    for i,s in enumerate(lsCard):
                        lsFile.append(f"{s}{ntal} {' '.join(card[i].split()[1:])}")

            # Remplissage de la categorie
            if "mcnp" not in self._dictElem.keys():
                self._dictElem["mcnp"] = lsFile
            else:
                self._dictElem["mcnp"].extend(lsFile)

        else:
            print("AddMCNPTally: Error.")
            print("Exit.")
            sys.exit()



    def AddMCNPPointTally(self, comment = "", group = "F5", part = "P", unit = "", card = [""], posgroup = "position", radiusgroup = "radius", ntal = -1):
        """
        AddMCNPPointTally(comment = "", group = "F5", part = "P", unit = "", fm = "", posgroup = "position", radiusgroup = "radius", ntal = -1):

        Function for adding point detectors of type F5 present in an MCNP file.
        The group must contain a field "trans" containing the number of the transformation
        applied to the whole file.

        Parametres :
            comment         : comment line to insert before the tally
            part            : particle of the tally ('P' or 'N')
            unit            : unit (ex: '*' for MeV/cm2)
            card            : list of tally data cards to add (ex: ["FM5 -1 -5 -6","FC5 scintillateur"])
            group           : name of the group containing the tally information
            posgroup        : name of the sub-category containing the list of points of the tally
                              of the form [x,y,z] or [[x1,y1,z1],[x2,y2,z2],...]
            radiusgroup     : radius of the sphere of the tally (in cm) for each point. If the list contains
                              only one value [r] for several points, then this value is duplicated.
            ntal            : number of the tally (determined automatically if left at -1).

        Exemple :
        obj.AddMCNPPointTally(part = "P", group = "F5_void", comment = "Detectors in void chamber")

        """

        # Construction du tally
        lsFile = list()
        if len(comment) > 0:
            lsFile.append("c " + comment)

        # Type de carte
        lsCard = list()
        if len(card) > 0 and len(card[0].strip()) > 0:
            for sCartInput in card:
                sCard = ""
                sCardNumber = ""
                for s in sCartInput.split()[0]:
                    # On recupere la description de la carte sauf le numéro de tally
                    if s.isdigit() is False:
                        sCard = sCard + s
                    else:
                        sCardNumber = sCardNumber + s
                lsCard.append(sCard)

                # Verification
                if len(sCardNumber) > 0 and sCardNumber[-1] != "5":
                    print("AddMCNPPointTally: Warning, input 'card' has a tally type different from 'F5'.")

        # Check groupe trans
        if self.CheckGroup(group,"trans"):
            tiDetNumTrans = self.GetGroup(group,"trans")

            # Boucle sur les transfos
            for iDetNumTrans in tiDetNumTrans:

                # Increment du numero du tally
                ntal = self._CheckMCNPTallyNumber(ntal,"F5",warning = 'off')

                # Check groupe F5
                if self.CheckGroup(group,posgroup) and self.CheckGroup(group,radiusgroup):
                    # On recupere les infos du groupe
                    npDetPos = np.array(self.GetGroup(group,posgroup),ndmin=2)
                    tdDetRadius = self.GetGroup(group,radiusgroup)

                    # On recupere la transfo associée
                    dictDetTr = self.FindTrCard(iDetNumTrans)

                    # Calcul matrice de rotation
                    npTransDetTr = np.array(dictDetTr["translat"])
                    npMatDetTr = np.array(dictDetTr["rot"]).reshape(3,3)
                    if dictDetTr["sens"] == -1:
                        dictDetTr["sens"] = 1
                        npTransDetTr = -npMatDetTr.T.dot(npTransDetTr)

                    # Verification
                    if np.shape(npDetPos)[0] < np.shape(tdDetRadius)[0]:
                        print(f"AddMCNPPointTally: Error, number of points {np.shape(npDetPos)} is less than number of radiuses {np.shape(tdDetRadius)} ")
                        print("Exit.")
                        sys.exit()
                    elif np.shape(npDetPos)[0] != np.shape(tdDetRadius)[0] and np.shape(tdDetRadius)[0] != 1:
                        print(f"AddMCNPPointTally: Error, number of points {np.shape(npDetPos)} and number of radiuses {np.shape(tdDetRadius)} are not the same.")
                        print("Exit.")
                        sys.exit()
                    elif np.shape(npDetPos)[0] > np.shape(tdDetRadius)[0] and np.shape(tdDetRadius)[0] == 1:
                        # On duplique les rayons
                        for i in range(1,np.shape(npDetPos)[0]):
                            tdDetRadius.append(tdDetRadius[0])

                    # On applique la transfo au vecteur position
                    for i in range(np.shape(npDetPos)[0]):

                        # Nouvel position du detecteur
                        npDetPosNew = (npMatDetTr.transpose()).dot(np.array(npDetPos[i]).transpose()) \
                                        + npTransDetTr

                        # Construction du tally
                        if i == 0:
                            sTal = f"{unit}F{ntal}:{part}"
                        else:
                            sTal = " "*5
                        lsFile.append(f"{sTal} {npDetPosNew[0]} {npDetPosNew[1]} {npDetPosNew[2]} {tdDetRadius[i]}")

                        # Ajout de la carte
                        if len(card) > 0 and len(card[0].strip()) > 0:
                            for i,s in enumerate(lsCard):
                                lsFile.append(f"{s}{ntal} {' '.join(card[i].split()[1:])}")

                else:
                    print(f"AddMCNPPointTally: Error, group '{group}' not found.")
                    print("Exit.")
                    sys.exit()

        else:
            print("AddMCNPPointTally: Error, group 'trans' not found.")
            print("Exit.")
            sys.exit()

        # Remplissage de la categorie
        if "mcnp" not in self._dictElem.keys():
            self._dictElem["mcnp"] = lsFile
        else:
            self._dictElem["mcnp"].extend(lsFile)

        return

    def AddMCNPBanner(self, banner):
        """
        AddMCNPBanner(banner):

        Function for inserting a banner in the input MCNP file.
        Useful for sectionning and organizing files.

        Example:
        obj.AddMCNPBanner("Tally definition")
        """

        # Banniere de separation
        lsFile = list()
        lsFile.append("c " + "="*78)
        if len(banner) > 0:
            lsFile.append("c " + banner.center(78))
        lsFile.append("c " + "="*78)

        # Remplissage de la categorie
        if "mcnp" not in self._dictElem.keys():
            self._dictElem["mcnp"] = lsFile
        else:
            self._dictElem["mcnp"].extend(lsFile)

        return
