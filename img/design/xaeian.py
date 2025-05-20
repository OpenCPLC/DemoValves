import os, sys, re, csv, json, stat, zipfile
from typing import Iterable, Any

#------------------------------------------------------------------------------ Files

FIX_PATH = False
ONEFILE_PACK = False

def FixPath(path:str, fix:bool|None=True, onefile_pack:bool|None=None) -> str:
  if fix is None: fix = FIX_PATH
  if onefile_pack is None: onefile_pack = ONEFILE_PACK
  if onefile_pack and hasattr(sys, '_MEIPASS'):
    path = os.path.join(sys._MEIPASS, path)
  path = path.replace("\\", "/")
  path = re.sub(r'/+', '/', path)
  while '/./' in path:
    path = path.replace('/./', '/')
  if not fix or os.path.isabs(path):
    return path
  path = ReplaceStart(path, "./", "")
  if getattr(sys, 'frozen', False):
    path = os.path.dirname(sys.executable).replace("\\", "/") + "/" + path
  elif __file__:
    path = os.path.dirname(__file__).replace("\\", "/") + "/" + path
  return path

def LocalPath(path:str, base:str|None=None, prefix:str="") -> str:
  path = os.path.abspath(path).replace("\\", "/")
  if base is None:
    if getattr(sys, 'frozen', False):
      base = os.path.dirname(sys.executable)
    else:
      try:
        base = os.path.dirname(os.path.abspath(__file__))
      except NameError:
        base = os.getcwd()
  base = os.path.abspath(base).replace("\\", "/")
  try:
    rel = os.path.relpath(path, base).replace("\\", "/")
    if not rel.startswith(".."):
      if prefix and not rel.startswith(prefix):
        rel = prefix + rel
      return rel
  except ValueError: pass
  return path

class DIR():

  @staticmethod
  def Create(path:str, fix:bool|None=None):
    path = FixPath(path, fix)
    if not os.path.exists(path): os.makedirs(path)

  @staticmethod
  def Exists(path:str, fix:bool|None=None, onefile_pack:bool|None=None):
    path = FixPath(path, fix, onefile_pack)
    if os.path.exists(path) and os.path.isdir(path): return True
    else: return False

  @staticmethod
  def _Force(path:str):
    os.chmod(path, stat.S_IWRITE)

  @staticmethod
  def Remove(path:str, fix:bool|None=None, force:bool=False):
    path = FixPath(path, fix)
    for root, dirs, files in os.walk(path, topdown=False):
      for file in files:
        full = os.path.join(root, file)
        if force: DIR._Force(full)
        os.remove(full)
      for dir in dirs:
        full = os.path.join(root, dir)
        if force: DIR._Force(full)
        os.rmdir(full)
    if force: DIR._Force(path)
    os.rmdir(path)
    
  @staticmethod
  def RemoveEmptyFolders(path:str, fix:bool|None=None, force:bool=False):
    path = FixPath(path, fix)
    if not DIR.Exists(path): return
    for root, dirs, _ in os.walk(path, topdown=False):
      for dir in dirs:
        full = os.path.join(root, dir)
        if not os.listdir(full):
          if force: DIR._Force(full)
          os.rmdir(full)
    if not os.listdir(path):
      if force: DIR._Force(path)
      os.rmdir(path)

  @staticmethod
  def Move(src:str, dst:str, fix:bool|None=None):
    src = FixPath(src, fix)
    dst = FixPath(dst, fix)
    if os.path.isdir(src):
      if not os.path.exists(dst):
        os.makedirs(dst)
      for root, dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        dst_dir = os.path.join(dst, rel)
        os.makedirs(dst_dir, exist_ok=True)
        for file in files:
          os.rename(os.path.join(root, file), os.path.join(dst_dir, file))
      DIR.Remove(src)
    else:
      os.rename(src, dst)

  @staticmethod
  def Copy(src:str, dst:str, fix:bool|None=None):
    src = FixPath(src, fix)
    dst = FixPath(dst, fix)
    if os.path.isdir(src):
      for root, dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        dst_dir = os.path.join(dst, rel)
        os.makedirs(dst_dir, exist_ok=True)
        for file in files:
          src_file = os.path.join(root, file)
          dst_file = os.path.join(dst_dir, file)
          with open(src_file, "rb") as fsrc:
            with open(dst_file, "wb") as fdst:
              fdst.write(fsrc.read())
    else:
      dst_dir = os.path.dirname(dst)
      if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
      with open(src, "rb") as fsrc:
        with open(dst, "wb") as fdst:
          fdst.write(fsrc.read())

  @staticmethod
  def FileList(path: str, exts: list[str] = [], blacklist: list[str] = [], fix: bool | None = None) -> list[str]:
    path = FixPath(path, fix)
    result = []
    blacklist = [FixPath(path + "/" + b, fix) for b in blacklist]
    exts = tuple(ext.lower() for ext in exts)
    for root, dirs, filelist in os.walk(path):
      root = FixPath(root, fix)
      if any(root.startswith(b) for b in blacklist):
        continue
      for name in filelist:
        if not exts or name.lower().endswith(exts):
          full_path = root + "/" + name
          result.append(full_path)

    return result

class FILE:

  @staticmethod
  def Exists(path:str, fix:bool|None=None, onefile_pack:bool|None=None) -> bool:
    path = FixPath(path, fix, onefile_pack)
    if os.path.exists(path) and os.path.isfile(path): return True
    else: return False

  @staticmethod
  def Remove(path:str, fix:bool|None=None, onefile_pack:bool|None=None) -> bool:
    path = FixPath(path, fix, onefile_pack)
    if FILE.Exists(path):
      os.remove(path)
      return True
    return False

  @staticmethod
  def Load(path:str, fix:bool|None=None, onefile_pack:bool|None=None, binary:bool=False) -> str|bytes:
    path = FixPath(path, fix, onefile_pack)
    if not os.path.exists(path): return b"" if binary else ""
    mode = "rb" if binary else "r"
    encoding = None if binary else "utf-8"
    try:
      with open(path, mode, encoding=encoding) as file: return file.read()
    except (OSError, TypeError) as e:
      print(f"Error loading file: {e}")
      return b"" if binary else ""

  @staticmethod
  def LoadLines(path:str, fix:bool|None=None, onefile_pack:bool|None=None) -> list[str]:
    path = FixPath(path, fix, onefile_pack)
    if not os.path.exists(path): return []
    try:
      with open(path, "r", encoding="utf-8") as file:
        return file.readlines()
    except Exception as e:
      print(f"Error loading text file: {e}")
      return []

  @staticmethod
  def Save(path:str, content:str|bytes, fix:bool|None=None):
    path = FixPath(path, fix)
    mode = "wb" if isinstance(content, bytes) else "w"
    encoding = None if mode == "wb" else "utf-8"
    try:
      with open(path, mode, encoding=encoding) as file: file.write(content)
    except (TypeError, OSError) as e:
      print(f"Error saving file: {e}")

class INI:

  @staticmethod
  def Load(path:str, fix:bool|None=None, onefile_pack:bool|None=None) -> dict:
    path = path.removesuffix('.ini') + '.ini'
    path = FixPath(path, fix, onefile_pack)
    if not os.path.exists(path): return {}
    try:
      with open(path, "r", encoding="utf-8") as file:
        content = file.read()
    except Exception:
      return {}
    content = re.sub(r"(;|#).*", "", content)
    content = re.sub(r"( *\r?\n *)+", "\n", content)
    lines = content.split("\n")
    ini = {}
    section = None
    for line in lines:
      line = line.strip()
      if not line:
        continue
      if line.startswith("[") and line.endswith("]"):
        section = line[1:-1].strip()
        ini[section] = {}
        continue
      key_value = line.split("=", 1)
      key = key_value[0].strip()
      value = key_value[1].strip() if len(key_value) > 1 else None
      if value:
        if (value[0] == value[-1]) and value[0] in ('"', "'"):
          value = value[1:-1]
        elif value.lower() == "true":
          value = True
        elif value.lower() == "false":
          value = False
        elif not value.startswith("+"):
          try:
            value = int(value, base=0)
          except ValueError:
            try:
              value = float(value)
            except ValueError:
              pass
      if section:
        ini[section][key] = value
      else:
        ini[key] = value
    return ini
  
  @staticmethod
  def Save(path:str, data:dict, fix:bool|None=None):
    path = path.removesuffix(".ini") + ".ini"
    path = FixPath(path, fix)
    try:
      with open(path, "w", encoding="utf-8") as file:
        for key, value in data.items():
          if isinstance(value, dict): # Section
            file.write(f"[{key}]\n")
            for sub_key, sub_value in value.items():
              if sub_value is None:
                file.write(f"{sub_key} =\n")
              elif isinstance(sub_value, str):
                file.write(f"{sub_key} = \"{sub_value}\"\n")
              elif isinstance(sub_value, (int, float)):
                file.write(f"{sub_key} = {sub_value}\n")
              else:
                raise ValueError(f"Unsupported value type for key '{sub_key}': {type(sub_value).__name__}")
          else: # Key-value pair outside any section
            if value is None:
              file.write(f"{key} =\n")
            elif isinstance(value, str):
              file.write(f"{key} = \"{value}\"\n")
            elif isinstance(value, (int, float)):
              file.write(f"{key} = {value}\n")
            else:
              raise ValueError(f"Unsupported value type for key '{key}': {type(value).__name__}")
    except Exception as e:
      print(f"Error saving INI file '{path}': {e}")

class CSV:

  @staticmethod
  def Load(path:str, delimiter:str=",", types:dict=None, fix:bool|None=None, onefile_pack:bool|None=None) -> list:
    path = path.removesuffix(".csv") + ".csv"
    path = FixPath(path, fix, onefile_pack)
    if not os.path.exists(path): return []
    try:
      with open(path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=delimiter)
        rows = []
        for row in reader:
          if types:
            for col, ctype in types.items():
              if col in row and row[col] not in (None, ""):
                try:
                  if ctype == int: row[col] = ctype(row[col], base=0)
                  else: row[col] = ctype(row[col])
                except (ValueError, TypeError):
                  print(f"Warning: Could not convert value '{row[col]}' in column '{col}' to {ctype.__name__}.")
                  row[col] = None
          rows.append(row)
        return rows
    except Exception as e:
      print(f"Error loading file '{path}': {e}")
      return []

  @staticmethod
  def AddRow(path:str, datarow:dict|list=[], fix:bool|None=None):
    path = path.removesuffix(".csv") + ".csv"
    path = FixPath(path, fix)
    file_exists = os.path.isfile(path)
    with open(path, "a", newline="", encoding="utf-8") as csv_file:
      if isinstance(datarow, dict):
        field_names = list(datarow.keys())
        writer = csv.DictWriter(csv_file, field_names=field_names)
        if not file_exists:
          writer.writeheader()
        writer.writerow(datarow)
      elif isinstance(datarow, list):
        writer = csv.writer(csv_file)
        writer.writerow(datarow)
      else:
        raise ValueError("Variable 'datarow' must be a dictionary or a list")

  @staticmethod
  def Save(path:str,data:list[dict]|list[list],field_names:list=None, fix:bool|None=None):
    path = path.removesuffix(".csv") + ".csv"
    path = FixPath(path, fix)
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
      if all(isinstance(row, dict) for row in data):
        field_names = field_names or list(data[0].keys())
        writer = csv.DictWriter(csv_file, field_names=field_names)
        writer.writeheader()
        writer.writerows(data)
      elif all(isinstance(row, list) for row in data):
        if not field_names:
          raise ValueError("Field names must be provided when saving lists")
        writer = csv.writer(csv_file)
        writer.writerow(field_names)
        writer.writerows(data)
      else:
        raise ValueError("Data must be a list of dictionaries or lists")

class JSON:

  @staticmethod
  def Load(path:str, otherwise: None|list|dict=None, fix:bool|None=None, onefile_pack:bool|None=None) -> dict|list|None:
    path = path.removesuffix(".json") + ".json"
    path = FixPath(path, fix, onefile_pack)
    if not os.path.isfile(path): return otherwise
    try:
      with open(path, "r", encoding="utf-8") as file:
        content = file.read()
        return json.loads(content) if content else otherwise
    except (json.JSONDecodeError, OSError) as e:
      print(f"Error loading JSON file '{path}': {e}")
      return otherwise

  @staticmethod
  def Save(path:str, content:dict|list|Any, fix:bool|None=None):
    path = path.removesuffix(".json") + ".json"
    path = FixPath(path, fix)
    try:
      with open(path, "w", encoding="utf-8") as file:
        json.dump(content, file, separators=(",", ":"))
    except (TypeError, OSError) as e:
      print(f"Error saving JSON file '{path}': {e}")

  @staticmethod
  def SavePretty(path:str, content:dict|list|Any, fix:bool|None=None):
    path = path.removesuffix(".json") + ".json"
    path = FixPath(path, fix)
    try:
      with open(path, "w", encoding="utf-8") as file:
        json.dump(content, file, indent=2, ensure_ascii=False)
    except (TypeError, OSError) as e:
      print(f"Error saving JSON file '{path}': {e}")


#------------------------------------------------------------------------------ ZIP

class ZIP():

  def Folder(path: str, zip_output: str | None = None):
    if zip_output is None:
      folder_name = os.path.basename(path)
      zip_output = os.path.join(path, folder_name + ".zip")
    zip_output = zip_output.removesuffix(".zip") + ".zip"
    with zipfile.ZipFile(zip_output, "w", zipfile.ZIP_DEFLATED) as zipf:
      for root, _, files in os.walk(path):
        for file in files:
          full_path = os.path.join(root, file)
          if full_path == zip_output: continue
          rel_path = os.path.relpath(full_path, path)
          zipf.write(full_path, rel_path)

#------------------------------------------------------------------------------ Str

def ReplaceStart(text:str, find:str, replace:str, border:bool=False):
  pattern = rf"(?m)^{re.escape(find)}{"\b" if border else ""}"
  return re.sub(pattern, replace, text)

def ReplaceEnd(text: str, find: str, replace: str, border:bool=False) -> str:
  pattern = rf"(?m){"\b" if border else ""}{re.escape(find)}$"
  return re.sub(pattern, replace, text)

def ReplaceMap(subject:str|list|dict, mapping:dict, prefix:str="", suffix:str=""):
  # Replace keys in the format prefix + key + suffix with values from the dictionary
  if isinstance(subject, str):
    for search, replace in mapping.items():
        subject = subject.replace(f"{prefix}{search}{suffix}", str(replace))
    return subject
  elif isinstance(subject, list):
    return [ReplaceMap(item, mapping, prefix, suffix) for item in subject]
  elif isinstance(subject, dict):
    return {key: ReplaceMap(value, mapping, prefix, suffix) for key, value in subject.items()}
  else:
    return subject

def SplitStr(string:str, split:str= " ", string_char:str='"', escape_char:str = "\\") -> list:
  def trim(value:str) -> str:
    if value[0] == string_char and value[-1] == string_char: return value[1:-1]
    else: return value
  array:list = []
  k:int = 0
  mute:bool = False
  mute_start:bool = False
  mute_end:bool = False
  escape:bool = False
  inc:int = 0
  count:int = len(split)
  val:str = ""
  i:int = 0
  while i < len(string):
    if string[i] == string_char:
      if not mute:
        mute_start = True
        mute = True
        if mute_end == True:
          array.append(trim(val))
          val = ""
    mute_end = False
    if not mute:
      j = 0
      go_continue = False
      while j < count:
        if string[i + j] == split[j]:
          if j + 1 == count:
            if not inc: val = trim(val)
            inc = 0
            k += 1
            array.append(val)
            val = ""
            i += j
            go_continue = True
            break # continue 2
        else:
          break
        j += 1
      if go_continue:
        i += 1
        continue
      inc += 1      
    if mute and not mute_start:
      if string[i] == escape_char: escape = True
      elif not escape and string[i] == string_char:
        mute = False
        mute_end = True
      else: escape = False
    if not escape:
      val += string[i]
    mute_start = False
    if i + 1 == len(string) and not inc:
      val = trim(val)
    i += 1
  array.append(val)
  return array

# test = 'Hello "world" this "\\"" is """ a" "test string" with "escape\\"s: " char'
# result = split_str(test)
# print(result)

def SplitSQL(sqls):
  sqls = SplitStr(sqls, ";", "'")
  for i, sql in enumerate(sqls):
    sql = re.sub(r"[\n\r]+", "", sql)
    sql = re.sub(r"[\ ]+", " ", sql)
    sql = re.sub(r"\ ?\(\ ?", "(", sql)
    sql = re.sub(r"\ ?\)\ ?", ")", sql)
    sql = re.sub(r"\ ?\,\ ?", ",", sql)
    sql = re.sub(r"\ ?\=\ ?", "=", sql)
    sqls[i] = sql
  output = []
  i = 0
  for sql in sqls:
    if sql and sql != " ":
      output.append(sql + ";")
      i += 1
  return output

def isUniform(lst:Iterable):
  return len(set(lst)) == 1

#------------------------------------------------------------------------------ Dict

class DICT():

  def FindMissingKeys(template:dict, subject:dict, prefix:str=""):
    missing = []
    for key in template:
      path = f"{prefix}.{key}" if prefix else key
      if key not in subject:
        missing.append(path)
      else:
        tval = template[key]
        sval = subject[key]
        if hasattr(tval, "keys") and hasattr(sval, "keys"):
          missing += DICT.FindMissingKeys(tval, sval, path)
    return missing

#------------------------------------------------------------------------------ Colors

class Color():
  RED = "\033[31m"
  GREEN = "\033[32m"
  BLUE = "\033[34m"
  YELLOW = "\033[33m"
  MAGENTA = "\033[35m"
  CYAN = "\033[36m"
  WHITE = "\033[37m"
  GREY = "\033[90m"
  ORANGE = "\033[38;2;206;145;120m"
  TEAL = "\033[38;2;32;178;170m"
  END = "\033[00m"

class IcoSymbols():
  INF = "💬"
  ERR = "🚨"
  WRN = "💡"
  OK  = "✅"
  DOC = "📄"
  RUN = "🚀"
  GAP = "\u3164"

class IcoText():
  INF = f"{Color.BLUE}INF{Color.END}"
  ERR = f"{Color.RED}ERR{Color.END}"
  WRN = f"{Color.YELLOW}WRN{Color.END}"
  OK  = f"{Color.GREEN}INF{Color.END}"
  DOC = f"{Color.MAGENTA}INF{Color.END}"
  RUN = f"{Color.ORANGE}RUN{Color.END}"
  GAP = "   "
  
#------------------------------------------------------------------------------
