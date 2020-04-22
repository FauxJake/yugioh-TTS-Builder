# todo steps
# 1. get list of cardnames from txt file DONE
# 2. get card info from ygopro api https://db.ygoprodeck.com/api/v7/cardinfo.php?name= DONE
# 3. parse info needed and add to decklist in memory DONE
# 4. create a bitmap based on decklist
# 5. upload bitmap
# 6. create TTS json file in %USER%/Documents/my games/Table Top Simulator/Saves/Saved Objects

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse, logging, sys, os, io, json, requests
from ftfy import fix_text
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

class TTSDeckbuilder():
    '''All the main deckbuilding logic goes here'''
    def __init__(self, filename, logger, imgurClientId):
        self._logger = logger
        self._filename = filename
        self._imgurClientId = imgurClientId

    class Card():
        '''represents and stores information about a single card'''
        def __init__(self, cardName):
            self._cardName = cardName
            self._metaDataUrl = "https://db.ygoprodeck.com/api/v7/cardinfo.php?name="
            self._ygoproId = -1
            self._desc = ""
            self._imageURL = ""

            self.populateDataFromYGoPro()

        def populateDataFromYGoPro(self):
            '''Gets metadata from YGoPro.org for a given cardname'''
            
            r = requests.get(fix_text(self._metaDataUrl + self._cardName.strip()))
            r.raise_for_status()
            responseJson = r.json()
            if "error" in responseJson and responseJson["error"]:
                raise CardNotFoundError(cardName=self._cardName)

            else:
                # populate some useful class info from the respose
                responseData = responseJson.get("data")[0] # going for exact names here
                self._ygoproId = responseData.get("id")
                self._desc = responseData.get("desc")
                self._imageURL = responseData.get("card_images")[0].get("image_url") # first printing, TODO - add option to randomize or specify printing

        def print(self):
            return json.dumps([self._cardName, self._ygoproId, self._desc, self._imageURL])


    def build(self):
        expandedDecklist = self.expandDecklistFromFile(args.filename, logging)
        deckWithData = self.getDeckData(expandedDecklist)
        image = self.createDeckImage(deckWithData)
        self.uploadImageToImgur(image)

    
    def expandDecklistFromFile(self, filename, logging):
        '''attempts to parse and return a list of expanded cardnames from the specified txt file'''
        self._logger.info("Expanding decklist from text file {0}...".format(filename))
        
        results = []
        with open(filename) as file:
            lines = list(file)
            for line in lines:
                line = fix_text(line.strip().rstrip("\n"))
                if line:
                    # need to expand multiples, format should be as "2 Dark Magician"
                    numCopies = line[0].strip()
                    cardName = line[1:].strip()
                    if cardName and numCopies:
                        j = int(numCopies)
                        while j > 0:
                            results.append(fix_text(cardName))
                            self._logger.debug("Added card {0}".format(cardName))
                            j-=1
                    else:
                        # formatting error
                        raise FormattingError(message="Unexpected format: {0}".format(line))    
        return results

    def getDeckData(self, expandedDecklist):
        '''Gets a json representation of the deck with information from ygopro.com'''
        self._logger.info("Creating deck metadata...")
            
        results = []
        for cardName in expandedDecklist:
            card = self.Card(cardName)
            results.append(card)
            self._logger.debug("Added card with metadata: {0}".format(card.print()))

        return results

    def createDeckImage(self, deckWithMetaData):
        '''creates an image to upload to imgur or store locally based on the cards in the deck'''
        self._logger.info("Generating deck image, this may take a hot sec...")
        
        images = []
        for card in deckWithMetaData:
            r = requests.get(card._imageURL, stream=True)
            r.raise_for_status()
            r.raw.decode_content = True
            images.append(r.raw) # store the bytes

        images = [Image.open(x) for x in images]

        widths, heights = zip(*(i.size for i in images))

        totalWidth = sum(widths)
        maxHeight = max(heights)

        result = Image.new('RGB', (totalWidth, maxHeight))

        x_offset = 0
        for im in images:
            result.paste(im, (x_offset,0))
            x_offset += im.size[0]

        result.save('test.jpg')

        return result

    def uploadImageToImgur(self, image):
        pass

def main(args, logLevel):
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logLevel)
    builder = TTSDeckbuilder(args.filename, logging, args.imgurClientId)
    builder.build()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
    description='A console tool for generating a Tabletop Simulator (TTS) Deck from a text file')

    # Positional Arguments
    parser.add_argument('filename',
                        help="The relative path to the text file containing the desired decklist. Each line in the " +
                            "file must be in the form of: 'N Cardname', where 'N' is the number of copies " +
                            "of the card to include")
    
    parser.add_argument('imgurClientId',
                        help="In order to upload images to imgur's API, you need to register your app here: https://api.imgur.com/oauth2/addclient, and feed me your clientID (or ask Jake nicely for his)")

    parser.add_argument(
                      "-v",
                      "--verbose",
                      help="increase output verbosity",
                      action="store_true")
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        logLevel = logging.DEBUG
    else:
        logLevel = logging.INFO

    args = parser.parse_args()
    main(args, logLevel)