import os
import shutil
from io import BytesIO

from PIL import Image
from tqdm import tqdm

from ebl.app import create_context
from ebl.errors import NotFoundError

if __name__ == "__main__":
    context = create_context()
    fragments_repository = context.fragment_repository
    fragments = fragments_repository.list_all_fragments()
    photo_repository = context.photo_repository
    no_images = 0
    output_folder_images = "images"
    if os.path.exists(output_folder_images):
        shutil.rmtree(output_folder_images)
    os.makedirs(output_folder_images)
    for fragment in tqdm(fragments):
        try:
            image = photo_repository.query_by_file_name(f"{fragment}.jpg")
            image_bytes = image.read()
            image = Image.open(BytesIO(image_bytes), mode="r")
            image.save(f"{output_folder_images}/{fragment}.jpg")
        except NotFoundError as e:
            # print(e)
            no_images += 1
            continue
    print(f"Number of fragments without images: {no_images}")
    print("Finished")
