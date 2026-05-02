from pydantic import BaseModel
import base64
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import torch
from torchvision import transforms
import torch.nn as nn
from torchvision import models
from PIL import Image
from io import BytesIO

app = FastAPI()

# Allow React to talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InputData(BaseModel):
    text: str

class ImageData(BaseModel):
    image: str
    filename: str = "pokemon.jpg"

classes = ['abra', 'absol', 'aerodactyl', 'aggron', 'aipom', 'alakazam', 'altaria', 'ampharos', 'anorith', 'arbok', 'arcanine', 'ariados', 'armaldo', 'aron', 'articuno', 'azumarill', 'azurill', 'bagon', 'baltoy', 'banette', 'barboach', 'bayleef', 'beautifly', 'beedrill', 'beldum', 'bellossom', 'bellsprout', 'blastoise', 'blaziken', 'blissey', 'breloom', 'bulbasaur', 'butterfree', 'cacnea', 'cacturne', 'camerupt', 'carvanha', 'cascoon', 'castform', 'caterpie', 'celebi', 'chansey', 'charizard', 'charmander', 'charmeleon', 'chikorita', 'chimecho', 'chinchou', 'clamperl', 'claydol', 'clefable', 'clefairy', 'cleffa', 'cloyster', 'combusken', 'corphish', 'corsola', 'cradily', 'crawdaunt', 'crobat', 'croconaw', 'cubone', 'cyndaquil', 'delcatty', 'delibird', 'deoxys', 'dewgong', 'diglett', 'ditto', 'dodrio', 'doduo', 'donphan', 'dragonair', 'dragonite', 'dratini', 'drowzee', 'dugtrio', 'dunsparce', 'dusclops', 'duskull', 'dustox', 'eevee', 'ekans', 'electabuzz', 'electrike', 'electrode', 'elekid', 'entei', 'espeon', 'exeggcute', 'exeggutor', 'exploud', 'farfetchd', 'fearow', 'feebas', 'feraligatr', 'flaaffy', 'flareon', 'flygon', 'forretress', 'furret', 'gardevoir', 'gastly', 'gengar', 'geodude', 'girafarig', 'glalie', 'gligar', 'gloom', 'golbat', 'goldeen', 'golduck', 'golem', 'gorebyss', 'granbull', 'graveler', 'grimer', 'groudon', 'grovyle', 'growlithe', 'grumpig', 'gulpin', 'gyarados', 'hariyama', 'haunter', 'heracross', 'hitmonchan', 'hitmonlee', 'hitmontop', 'ho-oh', 'hoothoot', 'hoppip', 'horsea', 'houndoom', 'houndour', 'huntail', 'hypno', 'igglybuff', 'illumise', 'ivysaur', 'jigglypuff', 'jirachi', 'jolteon', 'jumpluff', 'jynx', 'kabuto', 'kabutops', 'kadabra', 'kakuna', 'kangaskhan', 'kecleon', 'kingdra', 'kingler', 'kirlia', 'koffing', 'krabby', 'kyogre', 'lairon', 'lanturn', 'lapras', 'larvitar', 'latias', 'latios', 'ledian', 'ledyba', 'lickitung', 'lileep', 'linoone', 'lombre', 'lotad', 'loudred', 'ludicolo', 'lugia', 'lunatone', 'luvdisc', 'machamp', 'machoke', 'machop', 'magby', 'magcargo', 'magikarp', 'magmar', 'magnemite', 'magneton', 'makuhita', 'manectric', 'mankey', 'mantine', 'mareep', 'marill', 'marowak', 'marshtomp', 'masquerain', 'mawile', 'medicham', 'meditite', 'meganium', 'meowth', 'metagross', 'metang', 'metapod', 'mew', 'mewtwo', 'mightyena', 'milotic', 'miltank', 'minun', 'misdreavus', 'moltres', 'mr-mime', 'mudkip', 'muk', 'murkrow', 'natu', 'nidoking', 'nidoqueen', 'nidoran-f', 'nidoran-m', 'nidorina', 'nidorino', 'nincada', 'ninetales', 'ninjask', 'noctowl', 'nosepass', 'numel', 'nuzleaf', 'octillery', 'oddish', 'omanyte', 'omastar', 'onix', 'paras', 'parasect', 'pelipper', 'persian', 'phanpy', 'pichu', 'pidgeot', 'pidgeotto', 'pidgey', 'pikachu', 'piloswine', 'pineco', 'pinsir', 'plusle', 'politoed', 'poliwag', 'poliwhirl', 'poliwrath', 'ponyta', 'poochyena', 'porygon', 'porygon2', 'primeape', 'psyduck', 'pupitar', 'quagsire', 'quilava', 'qwilfish', 'raichu', 'raikou', 'ralts', 'rapidash', 'raticate', 'rattata', 'rayquaza', 'regice', 'regirock', 'registeel', 'relicanth', 'remoraid', 'rhydon', 'rhyhorn', 'roselia', 'sableye', 'salamence', 'sandshrew', 'sandslash', 'sceptile', 'scizor', 'scyther', 'seadra', 'seaking', 'sealeo', 'seedot', 'seel', 'sentret', 'seviper', 'sharpedo', 'shedinja', 'shelgon', 'shellder', 'shiftry', 'shroomish', 'shuckle', 'shuppet', 'silcoon', 'skarmory', 'skiploom', 'skitty', 'slaking', 'slakoth', 'slowbro', 'slowking', 'slowpoke', 'slugma', 'smeargle', 'smoochum', 'sneasel', 'snorlax', 'snorunt', 'snubbull', 'solrock', 'spearow', 'spheal', 'spinarak', 'spinda', 'spoink', 'squirtle', 'stantler', 'starmie', 'staryu', 'steelix', 'sudowoodo', 'suicune', 'sunflora', 'sunkern', 'surskit', 'swablu', 'swalot', 'swampert', 'swellow', 'swinub', 'taillow', 'tangela', 'tauros', 'teddiursa', 'tentacool', 'tentacruel', 'togepi', 'togetic', 'torchic', 'torkoal', 'totodile', 'trapinch', 'treecko', 'tropius', 'typhlosion', 'tyranitar', 'tyrogue', 'umbreon', 'unown', 'ursaring', 'vaporeon', 'venomoth', 'venonat', 'venusaur', 'vibrava', 'victreebel', 'vigoroth', 'vileplume', 'volbeat', 'voltorb', 'vulpix', 'wailmer', 'wailord', 'walrein', 'wartortle', 'weedle', 'weepinbell', 'weezing', 'whiscash', 'whismur', 'wigglytuff', 'wingull', 'wobbuffet', 'wooper', 'wurmple', 'wynaut', 'xatu', 'yanma', 'zangoose', 'zapdos', 'zigzagoon', 'zubat']
num_classes = len(classes)

device = "cuda" if torch.cuda.is_available() else "cpu"

model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)

# replace final classification layer
model.fc = nn.Linear(model.fc.in_features, num_classes)

print(device)

checkpoint = torch.load('RESbest_model.pth', weights_only=True, map_location=device)
model.load_state_dict(checkpoint)

model = model.to(device)
model.eval()

# FIXED: transform function should return the transformed image tensor
def preprocess_image(img):
    width, height = img.size

    # Determine the side length of the square (shortest side)
    size = min(width, height)

    # Calculate coordinates for central crop
    left = (width - size) / 2
    top = (height - size) / 2
    right = (width + size) / 2
    bottom = (height + size) / 2

    # Crop 
    img = img.crop((left, top, right, bottom))

    # Define the transformation pipeline
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # Added normalization for better accuracy
    ])

    # Return transformed image tensor
    return transform(img)

def predict(image):
    # Preprocess the image to get tensor
    image_tensor = preprocess_image(image)
    # Add batch dimension and move to device
    image_tensor = image_tensor.unsqueeze(0).to(device)
    
    with torch.no_grad():
        outputs = model(image_tensor)
        pred_idx = torch.argmax(outputs, dim=1).item()
        pred = classes[pred_idx]
    return pred

# Keep the original endpoint for multipart/form-data
@app.post("/api/predict")
async def upload_image(file: UploadFile = File(...)):
    try:
        print(f"Received file: {file.filename}")
        contents = await file.read()
        print(f"File size: {len(contents)} bytes")
        
        image = Image.open(BytesIO(contents)).convert('RGB')
        pred = predict(image)
        
        print(f"Prediction: {pred}")
        return {"Prediction": pred}
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# NEW: Base64 endpoint for React Native
@app.post("/api/predict-base64")
async def predict_base64(data: ImageData):
    try:
        print(f"Received base64 image, length: {len(data.image)}")
        
        # Remove data URL prefix if present
        if ',' in data.image:
            base64_str = data.image.split(',')[1]
        else:
            base64_str = data.image
        
        # Decode base64 to bytes
        image_bytes = base64.b64decode(base64_str)
        print(f"Decoded image size: {len(image_bytes)} bytes")
        
        # Convert to PIL Image
        image = Image.open(BytesIO(image_bytes)).convert('RGB')
        print(f"Image size: {image.size}")
        
        # Make prediction
        pred = predict(image)
        
        print(f"Prediction: {pred}")
        return {"Prediction": pred, "success": True}
        
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)