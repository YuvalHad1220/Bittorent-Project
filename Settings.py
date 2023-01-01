from dataclasses import dataclass, asdict
from json import dumps, loads
from utils import load_file, write_to_file, get_home_directory, get_cwd_directory, rand_str
@dataclass
class Settings:
    path: str
    default_download_path: str
    default_file_archive_path: str
    user_agent: str = "-qB4450-"
    random_id: str = rand_str(12)
    peer_id: str = "qBittorrent/4.4.5"
    port: int = 25565
    size_calc: str = "SI"
    max_torrentx_file_size: int = 15000000

    def asdict(self):
        self_dict = asdict(self)
        self_dict.pop('path')
        return self_dict

    def update(self):
        write_to_file(self.path, 'w', dumps(self.asdict(), indent=4))

    def update_settings(self, **kwargs):
        print(kwargs)
        self.default_download_path = kwargs['default_download_path']
        self.default_file_archive_path= kwargs['default_file_archive_path']
        self.port = kwargs['port']
        self.max_torrentx_file_size = kwargs['max_torrentx_file_size']
        self.size_calc = kwargs['size_calc']

        self.update()
def create_settings_file(path):
    default_download_path = get_home_directory() / "Downloads"
    default_download_path = default_download_path.as_posix()
    default_file_archive_path = get_cwd_directory() / "FileArchive"
    default_file_archive_path = default_file_archive_path.as_posix()
    settings = Settings(path, default_download_path, default_file_archive_path)
    settings.update()
    return settings

    
def read_settings_file(path):
    dic_file = load_file(path, 'r')
    if not dic_file:
        return create_settings_file(path)

    dic_file = loads(dic_file)
    return Settings(path = path, **dic_file)
