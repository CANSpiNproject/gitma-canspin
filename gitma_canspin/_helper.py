import os
import math
import yaml
from typing import Union, Dict, List, Tuple, Literal, Generator, Any

# defines some frequently used file paths
module_path: str = os.path.dirname(os.path.abspath(__file__))
abs_local_save_path: str = os.path.dirname(os.path.dirname(module_path))
projects_json_filepath: str = os.path.join(abs_local_save_path, 'gui_configs', 'projects.json')

class ConfigLoader:
    """Is used to load different yaml configuration files.
    It offers a basic loading functionality and is not designed for a specific configuration file with specific data structures.
    
    Args:
        filepath(str): A filepath pointing at an existing yaml configuration file.
    """
    def __init__(
            self,
            filepath: Union[str, None] = None):
        
        self.filepath = os.path.join(abs_local_save_path, 'api_configs', 'config.yaml') if not filepath else filepath
        self.is_valid_filepath: bool = os.path.isfile(self.filepath)

        if not self.is_valid_filepath:
            self.create_default_config()

        self.data = self.load()

    def create_default_config(self) -> None:
        makedir_if_necessary(os.path.join(abs_local_save_path, 'api_configs'))

        default_config_data: dict = {
            # maps catma project names to corpora repo folders in the project folder and languages
            'catma_projects': {
                'CATMA_5D2A90F0-4428-41CB-9D3A-E649CD1702C2_CANSpiN': 
                    {
                        'corpora_folders': ['canspin-deu-19', 'canspin-deu-20'], 
                        'languages': ['deu']
                    },
                'CATMA_3AA4ADC0-3C28-43F8-B5A0-9DCEFF23B90B_CANSpiN_Pilotanotationen_Spanisch': 
                    {
                        'corpora_folders': ['canspin-spa-19'], 
                        'languages': ['spa']
                    },
                'CATMA_3CA874CD-7E86-4FEA-9A33-0AB75CD9F374_CANSpiN_Annotationen_LAT19': 
                    {
                        'corpora_folders': ['canspin-lat-19'], 
                        'languages': ['spa']
                    },
                'CATMA_43E182B8-1908-413D-A1FE-EDDCDDE97A34_Space_DH_25': 
                    {
                        'corpora_folders': ['canspin-lat-19', 'canspin-spa-19'], 
                        'languages': ['spa']
                    },
                'CATMA_4AA4ADC0-4C28-54F9-B6A1-5DCEFF34B90B_DH2025_CANSpiN': 
                    {
                        'corpora_folders': ['canspin-deu-19', 'canspin-deu-20', 'canspin-lat-19', 'canspin-spa-19'], 
                        'languages': ['deu', 'spa']
                    }
            },
            # defines category and class systems which can be used in different methods and configurations
            'category_and_class_systems': {
                'CS1 v1.0.0 deu': {
                    'languages': ['deu'],
                    'categories': {
                        'Bewegung': '#B60000',
                        'Dimensionierung': '#7CD3C0',
                        'Ort': '#B6D3FF',
                        'Positionierung': '#DB8300',
                        'Richtung': '#92FFBD'
                    },
                    'classes': {
                        'Ort-Container': '#B6D3FF',
                        'Ort-Container-BK': '#CCDEFF',
                        'Ort-Objekt': '#D4EAFF',
                        'Ort-Objekt-BK': '#E6F2FF',
                        'Ort-Abstrakt': '#89A8F6',
                        'Ort-Abstrakt-BK': '#98C3FA',
                        'Ort-UE-XR': '#90A6C7',
                        'Ort-UE-RX': '#8093AD',
                        'Ort-UE-RR': '#6F8096',
                        'Bewegung-Subjekt': '#FF6D6D',
                        'Bewegung-Objekt': '#F60D00',
                        'Bewegung-Schall': '#FF4949',
                        'Bewegung-Licht': '#CA0B0B',
                        'Bewegung-Geruch': '#B60000',
                        'Bewegung-UE-XR': '#960000',
                        'Bewegung-UE-RX': '#7D0000',
                        'Bewegung-UE-RR': '#610000',
                        'Richtung': '#92FFBD',
                        'Richtung-UE-XR': '#75CC96',
                        'Richtung-UE-RX': '#69B584',
                        'Richtung-UE-RR': '#599970',
                        'Positionierung': '#DB8300',
                        'Positionierung-UE-XR': '#B56A01',
                        'Positionierung-UE-RX': '#995A02',
                        'Positionierung-UE-RR': '#804B01',
                        'Dimensionierung-Abstand': '#8AB6AD',
                        'Dimensionierung-Groesse': '#7CD3C0',
                        'Dimensionierung-Menge': '#7EF5D9',
                        'Dimensionierung-UE-XR': '#60847B',
                        'Dimensionierung-UE-RX': '#49615B',
                        'Dimensionierung-UE-RR': '#344541'
                    }
                },
                'CS1 v1.1.0 deu': {
                    'languages': ['deu'],
                    'categories': {
                        'Bewegung': '#B60000',
                        'Dimensionierung': '#7CD3C0',
                        'Ort': '#B6D3FF',
                        'Positionierung': '#DB8300',
                        'Richtung': '#92FFBD'
                    },
                    'classes': {
                        'Ort-Container': '#B6D3FF',
                        'Ort-Container-BK': '#CCDEFF',
                        'Ort-Objekt': '#D4EAFF',
                        'Ort-Objekt-BK': '#E6F2FF',
                        'Ort-Abstrakt': '#89A8F6',
                        'Ort-Abstrakt-BK': '#98C3FA',
                        'Ort-ALT': '#90A6C7',
                        'Bewegung-Subjekt': '#FF6D6D',
                        'Bewegung-Objekt': '#F60D00',
                        'Bewegung-Schall': '#FF4949',
                        'Bewegung-Licht': '#CA0B0B',
                        'Bewegung-Geruch': '#B60000',
                        'Bewegung-ALT': '#960000',
                        'Richtung': '#92FFBD',
                        'Richtung-ALT': '#75CC96',
                        'Positionierung': '#DB8300',
                        'Positionierung-ALT': '#B56A01',
                        'Dimensionierung-Abstand': '#8AB6AD',
                        'Dimensionierung-Groesse': '#7CD3C0',
                        'Dimensionierung-Menge': '#7EF5D9',
                        'Dimensionierung-ALT': '#60847B'
                    }
                },
                'CS1 v1.1.0 main_categories deu': {
                    'languages': ['deu'],
                    'categories': {
                        'Bewegung': '#B60000',
                        'Dimensionierung': '#7CD3C0',
                        'Ort': '#B6D3FF',
                        'Positionierung': '#DB8300',
                        'Richtung': '#92FFBD'
                    },
                    'classes': {
                        'Bewegung': '#B60000',
                        'Dimensionierung': '#7CD3C0',
                        'Ort': '#B6D3FF',
                        'Positionierung': '#DB8300',
                        'Richtung': '#92FFBD'
                    }
                },
                'CS1 v1.1.0 spa': {
                    'languages': ['spa'],
                    'categories': {
                        'Movimiento': '#B60000',
                        'Dimensionamiento': '#7CD3C0',
                        'Lugar': '#B6D3FF',
                        'Posicionamiento': '#DB8300',
                        'Dirección': '#92FFBD'
                    },
                    'classes': {
                        'Lugar-Contenedor': '#B6D3FF',
                        'Lugar-Contenedor-CM': '#CCDEFF',
                        'Lugar-Objeto': '#D4EAFF',
                        'Lugar-Objeto-CM': '#E6F2FF',
                        'Lugar-Abstracto': '#89A8F6',
                        'Lugar-Abstracto-CM': '#98C3FA',
                        'Lugar-ALT': '#90A6C7',
                        'Movimiento-Sujeto': '#FF6D6D',
                        'Movimiento-Objeto': '#F60D00',
                        'Movimiento-Sonido': '#FF4949',
                        'Movimiento-Luz': '#CA0B0B',
                        'Movimiento-Olfato': '#B60000',
                        'Movimiento-ALT': '#960000',
                        'Dirección': '#92FFBD',
                        'Dirección-ALT': '#75CC96',
                        'Posicionamiento': '#DB8300',
                        'Posicionamiento-ALT': '#B56A01',
                        'Dimensionamiento-Distancia': '#8AB6AD',
                        'Dimensionamiento-Tamaño': '#7CD3C0',
                        'Dimensionamiento-Cantitad': '#7EF5D9',
                        'Dimensionamiento-ALT': '#60847B'
                    }
                },
                'CS1 v1.1.0 main_categories spa': {
                    'languages': ['spa'],
                    'categories': {
                        'Movimiento': '#B60000',
                        'Dimensionamiento': '#7CD3C0',
                        'Lugar': '#B6D3FF',
                        'Posicionamiento': '#DB8300',
                        'Dirección': '#92FFBD'
                    },
                    'classes': {
                        'Lugar': '#B6D3FF',
                        'Movimiento': '#FF6D6D',
                        'Dirección': '#92FFBD',
                        'Posicionamiento': '#DB8300',
                        'Dimensionamiento': '#8AB6AD'
                    }
                },
                'spaceAN v1.0.0' : {
                    'languages': ['deu', 'spa'],
                    'categories': {
                        'CONTAINER': '#9dc3fd',
                        'OBJECT': '#7bf8d2',
                    },
                    'classes': {
                        'CONTAINER-ARTEFACT': '#9dc3fd',
                        'CONTAINER-NATURAL': '#7192c4',
                        'CONTAINER-REGION': '#4d678d',
                        'CONTAINER-SETTLEMENT': '#334663',
                        'OBJECT-ARTEFACT': '#7bf8d2',
                        'OBJECT-NATURAL': '#64b39b'
                    }
                }
            },
            # maps annotation schema designations to a category and class system designation defined in category_and_class_systems of this dict
            # different versions are not represented, it is assumed that always the newest version will be used
            'annotation_schema_mapping': {
                'cs1': [
                    'CS1 v1.1.0 deu', 
                    'CS1 v1.1.0 main_categories deu', 
                    'CS1 v1.1.0 spa', 
                    'CS1 v1.1.0 main_categories spa'
                ],
                'cs1_ntee': [
                    'CS1 v1.1.0 deu', 
                    'CS1 v1.1.0 main_categories deu', 
                    'CS1 v1.1.0 spa', 
                    'CS1 v1.1.0 main_categories spa'
                ],
                'cs1_gliner': [
                    'CS1 v1.1.0 deu', 
                    'CS1 v1.1.0 main_categories deu', 
                    'CS1 v1.1.0 spa', 
                    'CS1 v1.1.0 main_categories spa'
                ],
                'spaceAN': [
                    'spaceAN v1.0.0'
                ]
            },
            # translation dicts for German to English and Spanish to Englisch,
            # used in translate_dict function
            'eng_key_translation': {
                'CS1 v1.1.0 deu': {
                    'Ort-Container': 'Place-Container',
                    'Ort-Container-BK': 'Place-Container-MC',
                    'Ort-Objekt': 'Place-Object',
                    'Ort-Objekt-BK': 'Place-Object-MC',
                    'Ort-Abstrakt': 'Place-Abstract',
                    'Ort-Abstrakt-BK': 'Place-Abstract-MC',
                    'Ort-ALT': 'Place-ALT',
                    'Bewegung-Subjekt': 'Movement-Subject',
                    'Bewegung-Objekt': 'Movement-Object',
                    'Bewegung-Licht': 'Movement-Light',
                    'Bewegung-Schall': 'Movement-Sound',
                    'Bewegung-Geruch': 'Movement-Smell',
                    'Bewegung-ALT': 'Movement-ALT',
                    'Dimensionierung-Groesse': 'Dimensioning-Size',
                    'Dimensionierung-Abstand': 'Dimensioning-Distance',
                    'Dimensionierung-Menge': 'Dimensioning-Amount',
                    'Dimensionierung-ALT': 'Dimensioning-ALT',
                    'Positionierung': 'Positioning',
                    'Positionierung-ALT': 'Positioning-ALT',
                    'Richtung': 'Direction',
                    'Richtung-ALT': 'Direction-ALT'
                },
                'CS1 v1.1.0 main_categories deu': {
                    'Ort': 'Place',
                    'Bewegung': 'Movement',
                    'Dimensionierung': 'Dimensioning',
                    'Positionierung': 'Positioning',
                    'Richtung': 'Direction'
                },
                'CS1 v1.1.0 spa': {
                    'Lugar-Contenedor': 'Place-Container',
                    'Lugar-Contenedor-CM': 'Place-Container-MC',
                    'Lugar-Objeto': 'Place-Object',
                    'Lugar-Objeto-CM': 'Place-Object-MC',
                    'Lugar-Abstracto': 'Place-Abstract',
                    'Lugar-Abstracto-CM': 'Place-Abstract-MC',
                    'Lugar-ALT': 'Place-ALT',
                    'Movimiento-Sujeto': 'Movement-Subject',
                    'Movimiento-Objeto': 'Movement-Object',
                    'Movimiento-Luz': 'Movement-Light',
                    'Movimiento-Sonido': 'Movement-Sound',
                    'Movimiento-Olfato': 'Movement-Smell',
                    'Movimiento-ALT': 'Movement-ALT',
                    'Dimensionamiento-Tamaño': 'Dimensioning-Size',
                    'Dimensionamiento-Distancia': 'Dimensioning-Distance',
                    'Dimensionamiento-Cantitad': 'Dimensioning-Amount',
                    'Dimensionamiento-ALT': 'Dimensioning-ALT',
                    'Posicionamiento': 'Positioning',
                    'Posicionamiento-ALT': 'Positioning-ALT',
                    'Dirección': 'Direction',
                    'Dirección-ALT': 'Direction-ALT'
                },
                'CS1 v1.1.0 main_categories spa': {
                    'Lugar': 'Place',
                    'Movimiento': 'Movement',
                    'Dimensionamiento': 'Dimensioning',
                    'Posicionamiento': 'Positioning',
                    'Dirección': 'Direction'
                }
            }
        }

        with open(os.path.join(abs_local_save_path, 'api_configs', 'config.yaml'), 'w') as file:
            yaml.dump(default_config_data, file, default_flow_style=False, encoding='utf-8')

    def load(self) -> dict:
        result = {}

        with open(self.filepath, 'r', encoding='utf-8') as file:
            result = yaml.load(file, Loader=yaml.SafeLoader)

        return result

# lists the column titles of annotation tsv files in the canspin project; should stay hardcoded here due to dependency of different methods to this definition
canspin_annotation_tsv_columns: List[str] = [
    'Token_ID',
    'Text_Pointer',
    'Token',
    'Tag',
    'Annotation_ID',
    'Multi_Token_Annotation'
]

# helper functions
def makedir_if_necessary(directory: str) -> None:
    if not os.path.isdir(directory):
        os.makedirs(directory)

def dict_travel_generator(d: dict, type) -> Generator[Any, None, None]:
    if not d:
        yield None
    for value in d.values():
        if isinstance(value, dict):
            yield from dict_travel_generator(value, type)
        elif isinstance(value, type):
            yield value

def reduce_decimal_place(f: float, length: int) -> float:
    length = 1 if length < 1 else length
    return math.floor(f * (10 ** length)) / (10 ** length)

def prevent_division_by_zero(a: int, b: int) -> Union[float, int]:
    return a / b if b else 0

def translate_dict(input: dict, translation: dict) -> dict:
    translated: dict = dict([(translation.get(k, k), v) for k, v in input.items()])
    for key, value in translated.items():
        if isinstance(value, dict):
            translated[key] = translate_dict(value, translation)
    return translated
