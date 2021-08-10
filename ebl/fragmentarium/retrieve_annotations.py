import argparse
import os
import shutil
from io import BytesIO
from os.path import join
from urllib.request import urlopen

from PIL import Image
from dotenv import load_dotenv

from ebl.app import create_context
from ebl.context import Context
from ebl.files.application.file_repository import FileRepository
from ebl.fragmentarium.application.fragment_repository import FragmentRepository


def create_context_() -> Context:
    return create_context()

def retrieve_annotations(context: Context):
    annotation_repository = context.annotations_repository
    return annotation_repository.retrieve_all()

def calculate_bbox_coordinates(x, y, width, height):
    return [x,y, x+width, y, x+width, y+height, x, y+height ]


def convert_bboxes(shape, annotations):
    x_size = shape[0]
    y_size = shape[1]
    bboxes = []
    for bbox in annotations:
        new_x = int(round(bbox.geometry.x / 100 * x_size))
        new_y = int(round(bbox.geometry.y / 100 * y_size))
        new_width = int(round(bbox.geometry.width / 100 * x_size))
        new_height = int(round(bbox.geometry.height / 100 * y_size))
        bboxes.append(calculate_bbox_coordinates(new_x, new_y, new_width, new_height))
    return bboxes


def create_annotations(annotation_collection, output_folder_annotations, output_folder_images, fragment_repository: FragmentRepository, photo_repository: FileRepository):
    """
    creates icdar style annotations. Bounding boxes specified by x1,y1,x2,y2,x3,y3,x4,y4 clockwise vertices
    starting from top left
    original format from react-annotation tool is bottom left vertice and height and width values between 0 - 100
    relative to image size
    We compare number of annotations to transliteration so we can exclude annotaions which aren't complete
    """
    for counter, single_annotation in enumerate(annotation_collection):
        fragment_number = single_annotation.fragment_number
        fragment = fragment_repository.query_by_museum_number(single_annotation.fragment_number)
        signs_count = len(list(filter(lambda sign: "X" not in sign, fragment.signs.split())))
        annotations_count = len(single_annotation.annotations)
        print('{:>20}'.format(f"{fragment_number}/{fragment.cdli_number}"), '{:>4}'.format(
            f" {counter} of"), '{:>4}'.format(len(annotation_collection)), " signs count:", '{:>5}'.format(
            signs_count), " annotations_count", '{:>5}'.format(annotations_count))

        file_name_id, shape = save_image(fragment_number, fragment.cdli_number, output_folder_images, photo_repository)



        bboxes = convert_bboxes(shape, single_annotation.annotations)
        write_annotations(output_folder_annotations, f"gt_{file_name_id}.txt", bboxes)



def write_annotations(output_annotations, file_name, bboxes):
    txt_file = join(output_annotations, file_name)
    with open(txt_file, "w+") as file:
        for bbox in bboxes:
            vertices = ",".join(map(str, bbox))
            file.write(vertices+"\n")


def save_image(fragment_number, cdli_number, output_folder, photo_repository: FileRepository):
    """
    Some images are in our database, some aren't so we have to retrieve them from CDLI.
    Images from CDLI can have different shape than ours so if we can we try to retrieve them from our db
    """
    image_filename = f"{fragment_number}.jpg"
    if photo_repository.query_if_file_exists(image_filename):
        file_name_id = str(fragment_number)
        fragment_image = photo_repository.query_by_file_name(image_filename)
        image_bytes = fragment_image.read()
        image = Image.open(BytesIO(image_bytes), mode='r')
    else:
        file_name_id = cdli_number
        image_filename = f"{cdli_number}.jpg"
        image = Image.open(urlopen(f"https://cdli.ucla.edu/dl/photo/{image_filename}"))
    image.save(join(output_folder, image_filename))
    return file_name_id, image.size



def create_directory(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-oa", "--output_annotations", type=str, default=None, help="Output Annotations Directory",
    )
    parser.add_argument(
        "-oi", "--output_imgs", type=str, default=None, help="Output Images Directory",
    )
    args = parser.parse_args()

    if None not in (args.output_annotations, args.output_imgs):
        raise argparse.ArgumentError(None, message="Either specify both argument options or none at all")

    if args.output_annotations is None and args.output_imgs is None:
        create_directory("annotations")
        create_directory("annotations/annotations")
        create_directory("annotations/imgs")
        args.output_annotations = "annotations/annotations"
        args.output_imgs = "annotations/imgs"
    load_dotenv()
    context = create_context()
    annotation_collection = retrieve_annotations(context)
    create_annotations(annotation_collection, args.output_annotations, args.output_imgs, context.fragment_repository, context.photo_repository)
    print("Done")


