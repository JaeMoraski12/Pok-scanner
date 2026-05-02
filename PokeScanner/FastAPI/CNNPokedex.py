from pydantic import BaseModel
from fastapi import FastAPI
from fastapi import File, UploadFile
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
    allow_origins=["*"],  # for dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InputData(BaseModel):
    text: str

classes = ['abra', 'absol', 'aerodactyl', 'aggron', 'aipom', 'alakazam', 'altaria', 'ampharos', 'anorith', 'arbok', 'arcanine', 'ariados', 'armaldo', 'aron', 'articuno', 'azumarill', 'azurill', 'bagon', 'baltoy', 'banette', 'barboach', 'bayleef', 'beautifly', 'beedrill', 'beldum', 'bellossom', 'bellsprout', 'blastoise', 'blaziken', 'blissey', 'breloom', 'bulbasaur', 'butterfree', 'cacnea', 'cacturne', 'camerupt', 'carvanha', 'cascoon', 'castform', 'caterpie', 'celebi', 'chansey', 'charizard', 'charmander', 'charmeleon', 'chikorita', 'chimecho', 'chinchou', 'clamperl', 'claydol', 'clefable', 'clefairy', 'cleffa', 'cloyster', 'combusken', 'corphish', 'corsola', 'cradily', 'crawdaunt', 'crobat', 'croconaw', 'cubone', 'cyndaquil', 'delcatty', 'delibird', 'deoxys', 'dewgong', 'diglett', 'ditto', 'dodrio', 'doduo', 'donphan', 'dragonair', 'dragonite', 'dratini', 'drowzee', 'dugtrio', 'dunsparce', 'dusclops', 'duskull', 'dustox', 'eevee', 'ekans', 'electabuzz', 'electrike', 'electrode', 'elekid', 'entei', 'espeon', 'exeggcute', 'exeggutor', 'exploud', 'farfetchd', 'fearow', 'feebas', 'feraligatr', 'flaaffy', 'flareon', 'flygon', 'forretress', 'furret', 'gardevoir', 'gastly', 'gengar', 'geodude', 'girafarig', 'glalie', 'gligar', 'gloom', 'golbat', 'goldeen', 'golduck', 'golem', 'gorebyss', 'granbull', 'graveler', 'grimer', 'groudon', 'grovyle', 'growlithe', 'grumpig', 'gulpin', 'gyarados', 'hariyama', 'haunter', 'heracross', 'hitmonchan', 'hitmonlee', 'hitmontop', 'ho-oh', 'hoothoot', 'hoppip', 'horsea', 'houndoom', 'houndour', 'huntail', 'hypno', 'igglybuff', 'illumise', 'ivysaur', 'jigglypuff', 'jirachi', 'jolteon', 'jumpluff', 'jynx', 'kabuto', 'kabutops', 'kadabra', 'kakuna', 'kangaskhan', 'kecleon', 'kingdra', 'kingler', 'kirlia', 'koffing', 'krabby', 'kyogre', 'lairon', 'lanturn', 'lapras', 'larvitar', 'latias', 'latios', 'ledian', 'ledyba', 'lickitung', 'lileep', 'linoone', 'lombre', 'lotad', 'loudred', 'ludicolo', 'lugia', 'lunatone', 'luvdisc', 'machamp', 'machoke', 'machop', 'magby', 'magcargo', 'magikarp', 'magmar', 'magnemite', 'magneton', 'makuhita', 'manectric', 'mankey', 'mantine', 'mareep', 'marill', 'marowak', 'marshtomp', 'masquerain', 'mawile', 'medicham', 'meditite', 'meganium', 'meowth', 'metagross', 'metang', 'metapod', 'mew', 'mewtwo', 'mightyena', 'milotic', 'miltank', 'minun', 'misdreavus', 'moltres', 'mr-mime', 'mudkip', 'muk', 'murkrow', 'natu', 'nidoking', 'nidoqueen', 'nidoran-f', 'nidoran-m', 'nidorina', 'nidorino', 'nincada', 'ninetales', 'ninjask', 'noctowl', 'nosepass', 'numel', 'nuzleaf', 'octillery', 'oddish', 'omanyte', 'omastar', 'onix', 'paras', 'parasect', 'pelipper', 'persian', 'phanpy', 'pichu', 'pidgeot', 'pidgeotto', 'pidgey', 'pikachu', 'piloswine', 'pineco', 'pinsir', 'plusle', 'politoed', 'poliwag', 'poliwhirl', 'poliwrath', 'ponyta', 'poochyena', 'porygon', 'porygon2', 'primeape', 'psyduck', 'pupitar', 'quagsire', 'quilava', 'qwilfish', 'raichu', 'raikou', 'ralts', 'rapidash', 'raticate', 'rattata', 'rayquaza', 'regice', 'regirock', 'registeel', 'relicanth', 'remoraid', 'rhydon', 'rhyhorn', 'roselia', 'sableye', 'salamence', 'sandshrew', 'sandslash', 'sceptile', 'scizor', 'scyther', 'seadra', 'seaking', 'sealeo', 'seedot', 'seel', 'sentret', 'seviper', 'sharpedo', 'shedinja', 'shelgon', 'shellder', 'shiftry', 'shroomish', 'shuckle', 'shuppet', 'silcoon', 'skarmory', 'skiploom', 'skitty', 'slaking', 'slakoth', 'slowbro', 'slowking', 'slowpoke', 'slugma', 'smeargle', 'smoochum', 'sneasel', 'snorlax', 'snorunt', 'snubbull', 'solrock', 'spearow', 'spheal', 'spinarak', 'spinda', 'spoink', 'squirtle', 'stantler', 'starmie', 'staryu', 'steelix', 'sudowoodo', 'suicune', 'sunflora', 'sunkern', 'surskit', 'swablu', 'swalot', 'swampert', 'swellow', 'swinub', 'taillow', 'tangela', 'tauros', 'teddiursa', 'tentacool', 'tentacruel', 'togepi', 'togetic', 'torchic', 'torkoal', 'totodile', 'trapinch', 'treecko', 'tropius', 'typhlosion', 'tyranitar', 'tyrogue', 'umbreon', 'unown', 'ursaring', 'vaporeon', 'venomoth', 'venonat', 'venusaur', 'vibrava', 'victreebel', 'vigoroth', 'vileplume', 'volbeat', 'voltorb', 'vulpix', 'wailmer', 'wailord', 'walrein', 'wartortle', 'weedle', 'weepinbell', 'weezing', 'whiscash', 'whismur', 'wigglytuff', 'wingull', 'wobbuffet', 'wooper', 'wurmple', 'wynaut', 'xatu', 'yanma', 'zangoose', 'zapdos', 'zigzagoon', 'zubat']
num_classes = len(classes)

device = "cuda" if torch.cuda.is_available() else "cpu"

model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)

# replace final classification layer
model.fc = nn.Linear(model.fc.in_features, num_classes)


print(device)

checkpoint = torch.load('RESbest_model.pth', weights_only=True, map_location=device)
model.load_state_dict(checkpoint)
model.eval()

model = model.to(device)

model.eval()


def transformImg(img):
    width, height = img.size

    # Determine the side length of the square (shortest side)
    size = min(width, height)

    # Calculate coordinates for central crop
    left = (width - size) / 2
    top = (height - size) / 2
    right = (width + size) / 2
    bottom = (height + size) / 2

    # Crop and save
    img = img.crop((left, top, right, bottom))

    # 1. Define the transformation pipeline
    transform = transforms.Compose([
        transforms.Resize((224, 224)),      # Resize to  model's input size
        transforms.ToTensor(),           # Convert to [0, 1] range and tensor format
    ])

    return transform

def predict(image):
    image = transformImg(image).unsqueeze(0).to(device)
    with torch.no_grad():
        pred = classes[torch.argmax(model(image), dim=1).item()]  # Get predicted class index
    return pred


@app.post("/api/predict")
async def upload_image(file: UploadFile = File(...)):
    contents = await file.read()

    image = Image.open(BytesIO(contents)).convert('RGB')

    pred = predict(image)
    
    # run your model here
    return {"Prediction": pred}
