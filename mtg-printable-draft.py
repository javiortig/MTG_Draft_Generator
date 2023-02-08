import requests
from PIL import Image
from io import BytesIO
import os
import re
from bs4 import BeautifulSoup
from fpdf import FPDF
import shutil
from tkinter import Tk, messagebox     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askdirectory

a4_width, a4_height = int(21 * 96), int(29.7 * 96)
img_width, img_height = 672, 936

cols = a4_width // img_width
rows = a4_height // img_height

def getCardSetList(dir):
    with open(dir + "/Decklist-Arena.txt", "r") as file:
        text = file.read()

    lines = text.split("\n")

    cards_draft = [{
        "id": int(line.split()[-1]),
        "quantity": int(line.split()[0]),
        "set": re.search(r'\(([^)]+)\)', text).group(1).lower()
    } for line in lines if line]
    
    return cards_draft

def getImagesFromSet(cards_draft, dir):
    if not os.path.exists(dir + "/img"):
        os.makedirs(dir + "/img")
    else:
        return False
    
    for card in cards_draft:
        url = "https://scryfall.com/card/"+ card["set"] +"/"+ str(card["id"])
        downloadImage(url, dir + "/img" + "/" + str(card["id"]))

    return True

def downloadImage(url, dir):
    # Use the requests library to get the HTML content of the page
    response = requests.get(url)

    # Use BeautifulSoup to parse the HTML content
    soup = BeautifulSoup(response.content, "html.parser")

    # Find the div with the class "card-image-front"
    div = soup.find("div", {"class": "card-image-front"})

    # Find the image tag inside the div
    img_tag = div.find("img")

    # Get the image URL from the src attribute
    img_url = img_tag["src"]

    # Use the requests library to download the image
    img_response = requests.get(img_url)

    # Save the image to a file
    with open(dir + ".png", "wb") as f:
        f.write(img_response.content)

def get_image_files(directory):
    return [os.path.join(dir + "/img", f) for f in os.listdir(dir + "/img")]

def createSheets(setList, pdf_name, dir):
    # image_files = get_image_files(dir)
    # print("image_files en createSheets:")
    # for im in image_files:
    #     print(im)
    # print("\n\n")

    x, y, k = 0, 0, 0
    final_img = Image.new("RGB", (a4_width, a4_height), (255, 255, 255))
    lastSaved = False # to check that the last sheet was saved too. This happends if n_images // images_per_sheet == 0
    sheets = []
    for i in range(len(setList)):
        # Repeat j times, where j is the quantity
        for j in range(setList[i]["quantity"]):
            with Image.open(dir + "/img/" + str(setList[i]["id"]) + ".png") as im:
                print(f"i: {i}, setList[i]: {setList[i]}")

                lastSaved = False
                final_img.paste(im, (x, y))
                x += img_width
                # Reach X axis end, move to next y coord
                if x + img_width > a4_width:
                    x = 0
                    y += img_height

                # Reach Y axis end, create new sheet
                if y + img_height > a4_height:
                    #final_img.save("./final"+ str(k) +".jpg")
                    sheets.append(final_img)
                    k += 1
                    x, y = 0, 0
                    final_img = Image.new("RGB", (a4_width, a4_height), (255, 255, 255))
                    lastSaved = True

    if (not lastSaved):
        #final_img.save("./final"+ str(k) +".jpg")
        sheets.append(final_img)

    sheets[0].save(
        dir + "/"+ pdf_name +".pdf", "PDF" ,resolution=100.0, save_all=True, append_images=sheets[1:]
    )   

if __name__ == "__main__":
    # Ask for file
    print("1) Inicio")
    root = Tk()
    root.withdraw()
    dir = askdirectory(parent=root, title="Selecciona el directorio del draft, en el que se encuentra el Decklist-Arena.txt")
    print("El dir es: " + dir)

    print("2) Termina TK. Empieza getCardSetList")

    # Proccess card draft
    setList = getCardSetList(dir)
    print("3) Termina getCardSetList. Hemos obtenido la Lista:")
    print(setList)
    # Get the cards image
    print("--Hasta aqui parece que bien")
    print("4) Empieza getImagesFromSet:")

    # Get images. If file already exists, exception:
    if(not getImagesFromSet(setList, dir)):
        messagebox.showerror("ERROR", "Ya existe un directorio /img en el entorno de ejecucción.\n" +
         "Por favor, borre /img que se encuentra en: " + dir)
        quit()

    print("5) Empieza createSheets:")
    # Create a printable pdf from the images
    createSheets(setList, "imprimir", dir)

    # Removes the generated img folder
    shutil.rmtree(dir + "/img")

    # Destroys Tkinter
    root.destroy() 
