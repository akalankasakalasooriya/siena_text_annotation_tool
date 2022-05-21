from time import time
import yaml
import siena.server.DB.connection as db_conn
from bson.objectid import ObjectId
from bson.timestamp import Timestamp
import json
import datetime as dt
from bs4 import BeautifulSoup

knowledge = {}

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

#JSONEncoder().encode(objName)



def get_sentences(document_id,rangeStart,rangeEnd):
    document_id = ObjectId(document_id)
    SENTENCE = db_conn.get_connection().SENTENCE.find(
        {
            "$and":[ {"DOCUMENT_ID": document_id}, {"SENTENCE_NUMBER":{"$lte":rangeEnd}},{"SENTENCE_NUMBER":{"$gte":rangeStart}}]
        }
    )
    return list(SENTENCE)

def update_sentences_by_user(line_id, text,intent):
    document = []
    with open("inprogress.SIENA", "r", encoding='utf-8') as file:
        try:
            document = file.readlines()
            document[line_id] = intent + "<sep>" + text + '\n'
        except Exception as e:
            print(e)
            return False
    
    with open("inprogress.SIENA", "w", encoding='utf-8') as file:
        try:
            file.writelines(document)
        except Exception as e:
            print(e)
            return False
    return True
def update_knowledge(entity,highlighted):
    knowledge[highlighted] = entity
    return True

def delete_sentences(sentence_id):
    SENTENCE = db_conn.get_connection().SENTENCE
    query = { "_id": ObjectId(sentence_id) }
    SENTENCE.delete_one(query)
    return True

def read_yml(path_to_file,file_name):
    with open("config.SIENA", "w", encoding='utf-8') as file:
        try:
            file.write("file_name="+file_name+"\n")
        except Exception as exc:
            print(exc)
    data = {}
    with open(path_to_file, "r", encoding='utf-8') as stream:
        try:
            data = yaml.safe_load(stream)
            f = open("inprogress.SIENA", "w")
            f.write("")
            f.close()
        except yaml.YAMLError as exc:
            print(exc)

    intents = data["nlu"]
    for single_intent in intents:
        intent = single_intent['intent']
        examples = single_intent['examples'].split('\n')
        sentences = [i[2:] for i in examples]
        sentences = list(filter(lambda a: a != '', sentences))
        for sentence in sentences:
            for ch in ['(',')','[',']','{','}']:
                if ch in sentence:
                    sentence=sentence.replace(ch,"")
            line = intent + "<sep>" + sentence
            line = line.replace('\n','')
            with open("inprogress.SIENA", "a", encoding="utf-8") as f:
                f.write(line+"\n")


def get_entities_by_project():
    ENTITIES = []
    try:
        with open("entities.SIENA", encoding='utf-8') as file:
            line_id = 1
            while (line := file.readline().rstrip()):
                row = {}
                file_line = line.split('<sep>')
                row["ENTITY_NAME"]=file_line[0]
                row["ENTITY_REPLACER"]=file_line[1]
                row["ENTITY_COLOR"]=file_line[2]
                ENTITIES.append(row)
    except Exception as e:
        print(e)
        pass
    return ENTITIES

def get_suggestions(text):
    ENTITIES = []
    try:
        with open("entities.SIENA", encoding='utf-8') as file:
            while (line := file.readline().rstrip()):
                row = {}
                file_line = line.split('<sep>')
                row=file_line[0] #name of entity
                ENTITIES.append(row)
            
    except Exception as e:
        print(e)
        pass
    if text in knowledge.keys():
        result = knowledge[text]
        ENTITIES.remove(result)
        ENTITIES.insert(0,result)
        return ENTITIES

    else:
        print("no keys")
        return ENTITIES

def get_projects(userId):
    data = []
    cursor = db_conn.get_connection().PROJECT.find({"USER_ID": ObjectId(userId)})
    data = list(cursor)
    for index in range(len(data)):
        data[index]['CREATED_AT'] = str(data[index]['CREATED_AT'])

    return data

def create_project(user_id,project_name,project_type):
    data = {}
    data["USER_ID"]= ObjectId(user_id)
    data["NAME"]=project_name
    data["TYPE"]=project_type
    data["CREATED_AT"]= Timestamp(int(dt.datetime.today().timestamp()), 1)
    _id = ""
    try:
        _id =db_conn.get_connection().PROJECT.insert_one(data)
    except Exception:
        return False
    return _id.inserted_id

def create_document(project_id,name):
    data = {}
    data["USER_ID"]= ObjectId(project_id)
    data["NAME"]=name
    try:
        _id =db_conn.get_connection().PROJECT.insert_one(data)
    except Exception:
        return False
    return _id.inserted_id


def insert_entities_for_project(entities):
    with open("entities.SIENA", "w", encoding='utf-8') as file:
        text = ""
        try:
            for line in entities:
                text+=line['ENTITY_NAME']+"<sep>"+line['ENTITY_REPLACER']+"<sep>"+line['ENTITY_COLOR']+"\n"
            file.write(text)
        except Exception as e:
            print(e)
            return False
    return True

def get_files():
    data = []
    name = "undefined"
    with open("config.SIENA", encoding='utf-8') as file:
        while (line := file.readline().rstrip()):
            key,value = line.split('=')
            if key == "file_name":
                name = value
            else:
                continue
    data.append({'NAME':name})
    return data

def str_presenter(dumper, data):
  if len(data.splitlines()) > 1:  # check for multiline string
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
  return dumper.represent_scalar('tag:yaml.org,2002:str', data)

def convert_files():
    processed_yaml = {}
    file_name = get_files()[0]['NAME']
    inprogress_text = []
    with open("inprogress.SIENA", "r", encoding='utf-8') as file:
        try:
            inprogress_text = file.readlines()
        except Exception as e:
            print(e)
            return False

    formatted_text = []
    for document_line in inprogress_text:
        intent , text = document_line.split('<sep>')
        text = text.strip()
        intent = intent.strip()
        soup = BeautifulSoup(text, 'html.parser')
        input_tag = soup.find_all("div",{"name" : "highlighted"})
        sentence = ""
        if len(input_tag) > 0:
            for tag in input_tag:
                line = str(soup)
                attribute = tag.get('data')
                content = str(tag.text).strip()
                section = '[%s](%s) ' % (content,attribute)
                line = line.replace(str(tag), section, 1)
                sentence = line
        else:
            sentence = text
        # print("LINE :",sentence)
        if intent in processed_yaml.keys():
            processed_yaml[intent] += sentence+"\n- "
        else:
            processed_yaml[intent] = "\n"+sentence+"\n- "
    
    yaml.representer.SafeRepresenter.add_representer(str, str_presenter)
    with open("exports"+"\\"+file_name, "w", encoding='utf-8') as file:
        text = yaml.dump(processed_yaml, allow_unicode=True)
        try:
            # for line in formatted_text:
            #     text+=line+"\n- "
                
            file.write(text)
        except Exception as e:
            print(e)
            return False
    return True


    """
    -- Algorithms --
    1. SIENA reverse stemming
    2.
    3.
    """
def SIENA_reverse_stemming():
    

    return True