import os
import random
import string
import zipfile
import py7zr
import json
from config import TEMP_DIR

def generate_random_id(length=8):
    """Generate random ID for temp files"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

class FileProcessor:
    def __init__(self):
        self.temp_dir = TEMP_DIR

    def create_archive(self, file_paths, output_path, archive_type='zip', password=None):
        """Create archive file (zip, rar, 7z)"""
        if archive_type == 'zip':
            with zipfile.ZipFile(output_path, 'w') as zipf:
                for file_path in file_paths:
                    zipf.write(file_path, os.path.basename(file_path))
                    if password:
                        zipf.setpassword(password.encode())
        
        elif archive_type == '7z':
            with py7zr.SevenZipFile(output_path, 'w', password=password) as archive:
                for file_path in file_paths:
                    archive.write(file_path, os.path.basename(file_path))
        
        return output_path

    def extract_archive(self, archive_path, output_dir, password=None):
        """Extract archive file"""
        extracted_files = []
        
        if archive_path.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                if password:
                    zipf.setpassword(password.encode())
                zipf.extractall(output_dir)
                extracted_files = zipf.namelist()
        
        elif archive_path.endswith('.7z'):
            with py7zr.SevenZipFile(archive_path, 'r', password=password) as archive:
                archive.extractall(output_dir)
                extracted_files = archive.getnames()
        
        return [os.path.join(output_dir, f) for f in extracted_files]

    def convert_subtitle(self, input_path, output_path, format_type):
        """Convert subtitle format"""
        # For simplicity, just copy the file with new extension
        # In real implementation, you'd use proper subtitle conversion
        with open(input_path, 'r', encoding='utf-8') as f_in:
            content = f_in.read()
        
        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.write(content)
        
        return output_path

    def format_json(self, input_path, output_path, indent=4):
        """Format JSON file with specified indentation"""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        
        return output_path

    def remove_forwarded_tag(self, file_path):
        """Remove forwarded tag (placeholder)"""
        # This would require modifying Telegram metadata which isn't directly accessible
        # For now, just return the original file path
        return file_path
