from ebl.app import create_context
from ebl.fragmentarium.application.annotations_service import AnnotationsService

if __name__ == "__main__":
    context = create_context()
    annotations = context.annotations_repository.retrieve_all_non_empty()
    service = AnnotationsService(
        context.ebl_ai_client,
        context.annotations_repository,
        context.photo_repository,
        context.changelog,
        context.fragment_repository,
        context.photo_repository,
        context.cropped_sign_images_repository,
    )
    for counter, annotation in enumerate(annotations):
        print(f"Lenght {len(annotations)}")
        try:
            print(counter)
            print(annotation.fragment_number)
            service.update_(annotation)
            print()
        except Exception as e:
            print(e)

    print("Update fragments completed!")
