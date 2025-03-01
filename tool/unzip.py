import tarfile
import os

folder_path = r"D:\KG_LLM\Database\latex"
destination_folder = "./latex/"
papers = os.listdir(folder_path)
file_list = [paper for paper in papers if os.path.isfile(os.path.join(folder_path, paper))]
print(file_list)

for file_path in file_list:
    file_path = folder_path + file_path
    print(file_path)
    with tarfile.open(file_path, 'r:gz') as tar:
        for member in tar.getmembers():
            if member.isfile() and member.name.endswith(".tex"):
                tar.extract(member, path=destination_folder)
