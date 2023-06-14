import os
from os import path
from argparse import ArgumentParser
import glob
import cv2


class GHTitleCropper:
    RESERVED_FILE_PREFIXES = ["TRANSFORMED", "PREVIEW"]

    LETTER_MAX_WIDTH = 29
    LETTER_MIN_WIDTH = 5  # LA "I" DE MIERDA

    LETTER_MAX_HEIGHT = 35
    LETTER_MIN_HEIGHT = 27

    MIN_Y_OFFSET = 77

    @staticmethod
    def transform_img(img):
        grey_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        threshold_img = cv2.threshold(grey_img, 198, 255, cv2.THRESH_BINARY_INV)[1]
        adaptive_threshold = cv2.adaptiveThreshold(threshold_img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 11, 3)

        return adaptive_threshold

    @staticmethod
    def filter_contours(img):
        contours, _ = cv2.findContours(img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        text_min_y = img.shape[0] / 2 + GHTitleCropper.MIN_Y_OFFSET

        filtered_cnts_points = []

        for cnt in contours:
            x, y, width, height = cv2.boundingRect(cnt)

            if y < text_min_y:
                continue
            
            if (
                (GHTitleCropper.LETTER_MAX_WIDTH > width >= GHTitleCropper.LETTER_MIN_WIDTH) and
                (GHTitleCropper.LETTER_MAX_HEIGHT > height >= GHTitleCropper.LETTER_MIN_HEIGHT)
            ):
                filtered_cnts_points.append((x, y))
        
        return filtered_cnts_points
    
    @staticmethod
    def is_in_palette(r, g, b):
        return 40 < r < 123 and g < 100 and 40 < b < 180
    
    @staticmethod
    def crop_title(file_path, save_verbal=False):
        file_name = path.splitext(path.basename(file_path))[0]

        original_img = cv2.imread(file_path)

        if original_img is None:
            raise ValueError("pelotudo de mierda")
        
        transformed_img = GHTitleCropper.transform_img(original_img)

        cnts_points = GHTitleCropper.filter_contours(transformed_img)

        if not len(cnts_points):
            print(f"No se encontraron contornos interesantes en `{file_name}`.")
            return

        # min_y = max_y, nunca dije q no sea útil eh # ??
        min_x, min_y = min(cnts_points, key=lambda point: point[0])
        max_x, max_y = max(cnts_points, key=lambda point: point[0])

        # check adicional cause why not?
        if max_x - min_x < 100:
            print(f"Se detecto falso-positivo en `{file_name}`, pero sigue sin ser un contorno interesante kjj.")
            return

        cv2.imwrite(
            path.join("results", file_name + "_TRANSFORMED.jpg"),
            original_img[min_y:max_y + GHTitleCropper.LETTER_MAX_HEIGHT, min_x:max_x + GHTitleCropper.LETTER_MAX_WIDTH],
            [cv2.IMWRITE_JPEG_QUALITY, 90]
        )

        if save_verbal:
            TEXT_OFFSET = 10

            MIDDLE_X = (min_x + max_x) // 2 - TEXT_OFFSET * 20
            MIDDLE_Y = (min_y + max_y) // 2 - TEXT_OFFSET

            copied_img = original_img.copy()

            cv2.putText(
                copied_img,
                "PETEFE LA CONCHA DE TU MADRE",
                (MIDDLE_X, MIDDLE_Y),
                cv2.FONT_HERSHEY_PLAIN,
                1.5,
                (0, 255, 0),
                2
            )

            cv2.rectangle(
                copied_img,
                (min_x, min_y),
                (max_x + GHTitleCropper.LETTER_MAX_WIDTH, min_y + GHTitleCropper.LETTER_MAX_HEIGHT),
                (0, 255, 0),
                3
            )

            cv2.imwrite(
                path.join("results", file_name + "_PREVIEW.png"),
                copied_img
            )


def transform_moment():
    dir_files = glob.glob("input-imgs/*")

    if len(dir_files):
        if not path.exists("results"):
            os.makedirs("results")

        for file_path in dir_files:
            lowered_path = file_path.lower()

            if ((".jpg" in lowered_path or ".png" in lowered_path) and 
                not any(prefix in lowered_path for prefix in GHTitleCropper.RESERVED_FILE_PREFIXES)):
                GHTitleCropper.crop_title(file_path, save_verbal=True)
    else:
        print("No se encontraron imágenes de input?")


def check_for_interruption(img):
    # para mejor matching hehe
    img = GHTitleCropper.transform_img(img)

    img = img[img.shape[0] // 2 + GHTitleCropper.MIN_Y_OFFSET:img.shape[0], 0:img.shape[1]]

    dir_files = glob.glob("results/*_TRANSFORMED.jpg")

    text_templates = []

    for file_path in dir_files:
        template_img = cv2.imread(file_path)

        if template_img is not None:
            text_templates.append(GHTitleCropper.transform_img(template_img))
    
    matching_results = []

    for template in text_templates:
        match_result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)

        _, max_val, _, _ = cv2.minMaxLoc(match_result)

        coincidence_percent = round(max_val, 2) * 100

        matching_results.append(coincidence_percent)
    
    is_probably = any(percent >= 83.67 for percent in matching_results)
    max_percent = max(matching_results)

    if not is_probably:
        print("No se encontró nada.")
    
    else:
        print("Está en un momento del morbo.")
    
    print(f"El % de coincidencia más alto fue del {max_percent}% btw.")


def main():
    parser = ArgumentParser(description="GH's morbo-moment recognition")
    parser.add_argument('-t', '--transform', action='store_true', help="Extraer los textos de las imágenes y esas weas")
    parser.add_argument('-d', '--detect', type=str, help="Testear si en un frame no está el reality")

    args = parser.parse_args()

    if args.transform:
        transform_moment()
    
    elif args.detect:
        frame_img = cv2.imread(args.detect)

        if frame_img is not None:
            check_for_interruption(frame_img)
        
        else:
            print(f"Al menos pasá una imagen q exista amigo: {args.detect}")
    
    else:
        print("ok ig?")


if __name__ == '__main__':
    main()
