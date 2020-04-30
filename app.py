# todo steps
# 7. Package as setup-tools .exe
# 8. QoL stuff like deck name, etc.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse, logging, sys, os, io, json, requests
import PySimpleGUI as sgui
# from ftfy import fix_text
from PIL import Image

__author__ = "Jake Riesser"
__license__ = """/*
 * ----------------------------------------------------------------------------
 * "THE BEER-WARE LICENSE" (Revision 42):
 * <Jake.Riesser@Gmail.com> wrote this file.  As long as you retain this notice you
 * can do whatever you want with this stuff. If we meet some day, and you think
 * this stuff is worth it, you can buy me a beer in return.   Poul-Henning Kamp
 * ----------------------------------------------------------------------------
 */"""
__version__ = "0.0.1"
__maintainer__ = "Jake.Riesser@Gmail.com"
__email__ = "Jake.Riesser@Gmail.com"
__status__ = "Development"


class Error(Exception):
    """Base class for exceptions in this module."""

    pass


class FormattingError(Error):
    """Exception raised for errors in the input text file.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message


class CardNotFoundError(Error):
    """Exception raised when a card is not found on YGOPro.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, cardName):
        self.cardName = cardName
        self.message = "Cannot find the card {0} on YGoPro".format(self.cardName)


class TTSDeckbuilder:
    """All the main deckbuilding logic goes here"""

    def __init__(self, fileName, deckName, logger):
        self._logger = logger
        self._fileName = fileName
        self._deckName = deckName
        # self._imgurClientId = imgurClientId
        self._imgurUploadUrl = "https://api.imgur.com/3/upload"

    class Card:
        """represents and stores information about a single card"""

        def __init__(self, cardName):
            self._cardName = cardName
            self._metaDataUrl = "https://db.ygoprodeck.com/api/v7/cardinfo.php?name="
            self._ygoproId = -1
            self._deckID = -1
            self._desc = ""
            self._imageURL = ""

            self.populateDataFromYGoPro()

        def populateDataFromYGoPro(self):
            """Gets metadata from YGoPro.org for a given cardname"""

            r = requests.get(self._metaDataUrl + self._cardName.strip())
            r.raise_for_status()
            responseJson = r.json()
            if "error" in responseJson and responseJson["error"]:
                raise CardNotFoundError(cardName=self._cardName)

            else:
                # populate some useful class info from the respose
                responseData = responseJson.get("data")[0]  # going for exact names here
                self._ygoproId = responseData.get("id")
                self._desc = responseData.get("desc")
                self._imageURL = responseData.get("card_images")[0].get(
                    "image_url"
                )  # first printing, TODO - add option to randomize or specify printing

        def print(self):
            return json.dumps(
                [self._cardName, self._ygoproId, self._desc, self._imageURL]
            )

    def build(self):
        expandedDecklist = self.expandDecklistFromFile(self._fileName, logging)
        deckWithData = self.getDeckData(expandedDecklist)
        self.assignDeckIDs(deckWithData)
        # image = self.createDeckImage(deckWithData)
        # self.uploadImageToImgur(image)
        self.createTTSFile(deckWithData)

    def expandDecklistFromFile(self, filename, logging):
        """attempts to parse and return a list of expanded cardnames from the specified txt file"""
        self._logger.info("Expanding decklist from text file {0}...".format(filename))

        results = []
        with open(filename) as file:
            lines = list(file)
            for line in lines:
                line = line.strip().rstrip("\n")
                if line:
                    # need to expand multiples, format should be as "2 Dark Magician"
                    numCopies = line[0].strip()
                    cardName = line[1:].strip()
                    if cardName and numCopies:
                        j = int(numCopies)
                        while j > 0:
                            results.append(cardName)
                            self._logger.debug("Added card {0}".format(cardName))
                            j -= 1
                    else:
                        # formatting error
                        raise FormattingError(
                            message="Unexpected format: {0}".format(line)
                        )
        return results

    def getDeckData(self, expandedDecklist):
        """Gets a json representation of the deck with information from ygopro.com"""
        self._logger.info("Creating deck metadata...")

        results = []
        for cardName in expandedDecklist:
            card = self.Card(cardName)
            results.append(card)
            self._logger.debug("Added card with metadata: {0}".format(card.print()))

        return results

    def assignDeckIDs(self, deck):
        """assigns a unique deckID for TTS use. Like cards should have the same ID"""
        ctr = 100  # increments by 100s
        for card in deck:
            if card._deckID == -1:
                card._deckID = ctr
                Id = card._ygoproId
                for c in deck:  # all copies of the card should have the same deckID
                    if c._ygoproId == Id:
                        c._deckID = ctr
                ctr += 100

    def createDeckImage(self, deckWithMetaData):
        """creates an image to upload to imgur or store locally based on the cards in the deck"""
        self._logger.info("Generating deck image, this may take a hot sec...")

        images = []
        for card in deckWithMetaData:
            r = requests.get(card._imageURL, stream=True)
            r.raise_for_status()
            r.raw.decode_content = True
            images.append(r.raw)  # store the bytes

        images = [Image.open(x) for x in images]

        widths, heights = zip(*(i.size for i in images))

        totalWidth = sum(widths)
        maxHeight = max(heights)

        result = Image.new("RGB", (totalWidth, maxHeight))

        x_offset = 0
        for im in images:
            result.paste(im, (x_offset, 0))
            x_offset += im.size[0]

        result.save("test.jpg")

        return result

    def createTTSFile(self, deck):
        """generates a json file and saves it to disk for importing into TTS
        ObjectStates
            [{
                Name:
                ContainedObjects:
                [{
                    {CardID, Name, NickName, Transform} < -- each card needs one of these
                }],
                DeckIDs: [], < -- deck distrubution (100 = 1 below, increment by 100s)
                CustomDeck: { < -- card data
                    1 : {
                        FaceUrl, 
                        BackUrl,
                        NumHeight,
                        NumWidth,
                        BackIsHidden : True
                    },
                    Transform
                }
            }]
        
        """
        Transform = {
            "posX": 0,
            "posY": 0,
            "posZ": 0,
            "rotX": 0,
            "rotY": 180,
            "rotZ": 180,
            "scaleX": 1,
            "scaleY": 1,
            "scaleZ": 1,
        }

        TTSDeck = []
        for card in deck:
            TTSDeck.append(
                {
                    "CardID": card._deckID,
                    "Name": "Card",
                    "Nickname": card._cardName,
                    "Transform": Transform,
                }
            )

        DeckIDs = []
        for card in deck:
            DeckIDs.append(card._deckID)

        CustomDeck = {}
        for card in deck:
            if str(int(card._deckID / 100)) not in CustomDeck.keys():
                CustomDeck[str(int(card._deckID / 100))] = {
                    "FaceURL": card._imageURL,
                    "BackURL": "https://i.imgur.com/ubLQ2p2.jpg",
                    "NumHeight": 1,
                    "NumWidth": 1,
                    "BackIsHidden": True,
                }

        # construct the json object
        TTS = {}  # base object
        ObjectStates = []
        ObjectStates.append(
            {
                "Name": "DeckCustom",
                "ContainedObjects": TTSDeck,
                "DeckIDs": DeckIDs,
                "CustomDeck": CustomDeck,
                "Transform": Transform,
            }
        )
        TTS["ObjectStates"] = ObjectStates
        self._logger.debug(json.dumps(TTS))
        with open(self._deckName + ".json", "w") as outFile:
            json.dump(TTS, outFile)


def main(fileName, deckName, logLevel):
    logging.basicConfig(filename="application.log", filemode="w", format="%(levelname)s: %(message)s", level=logLevel)
    builder = TTSDeckbuilder(fileName, deckName, logging)
    builder.build()


if __name__ == "__main__":
    sgui.theme("Dark")
    layout = [
        [sgui.Text("Select a decklist to convert: ")],
        [sgui.Input(key="FILE"), sgui.FilesBrowse()],
        [sgui.Text("Name the Deck: ")],
        [sgui.Input(key="NAME")],
        [sgui.Checkbox("Debug Mode", key="DEBUG")],
        [sgui.Submit()],
    ]

    window = sgui.Window("TTS Yu-Gi-Oh Deckbuilder", layout)
    events, values = window.read()

    # Setup logging
    if values["DEBUG"]:
        logLevel = logging.DEBUG
    else:
        logLevel = logging.INFO

    # args = parser.parse_args()
    main(values["FILE"], values["NAME"], logLevel)
    sgui.popup_ok("Drag the {0}.json file into My Documents/my games/TableTop Simulator/Saves/Saved Objects and you should be gtg.".format(values["NAME"]), title="Deck Created")
