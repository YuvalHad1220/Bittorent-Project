from dataclasses import dataclass, asdict
from json import dumps, loads
from utils import load_file, write_to_file, get_home_directory
@dataclass
class Settings:
    path: str
    default_download_path: str
    port: int = 25565
    size_calc: str = "si"
    max_torrentx_file_size: int = 15000000

    def asdict(self):
        self_dict = asdict(self)
        self_dict['default_download_path'] = self_dict['default_download_path'].as_posix()
        self_dict.pop('path')
        return self_dict

    def update(self):
        write_to_file(self.path, 'w', dumps(self.asdict()))

def create_settings_file(path):
    default_download_path = get_home_directory() / "Downloads"
    settings = Settings(path, default_download_path)
    settings.update()
    return settings

    
def read_settings_file(path):
    dic_file = load_file(path, 'r')
    dic_file = loads(dic_file)
    
    return Settings(path = path, **dic_file)