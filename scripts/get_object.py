from ultralytics import YOLO
import cv2
from scripts.get_odometer import get_odometer
from scripts.get_serial_num import get_serial_num
import contextlib
import io

# Carregar o modelo YOLO
model = YOLO('/root/Anemovision/models/ObjectFinder_v3.pt')

def get_objects(img_path, confidence_threshold=0.80, iou_threshold=0.5):
    img = cv2.imread(img_path)

    # Dicionário de limites de confiança específicos para classes
    specific_confidences = {
        "painel-carro": 0.85,
        "windvane": 0.60,
        "numero-serie": 0.76,
        "carro": 0.80
    }

    # Redirecionar a saída padrão para um buffer temporário
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        # Fazer a inferência na imagem com os parâmetros de confiança e sobreposição
        results = model(img, conf=confidence_threshold, iou=iou_threshold)

    # Lista para armazenar os resultados
    objects_info = []

    # Processar os resultados
    for result in results:
        for detection in result.boxes.data.tolist():
            x1, y1, x2, y2, confidence, class_id = detection

            # Obter o nome da classe
            object_name = model.names[int(class_id)]

            # Verificação de confiança específica para classes
            if object_name in specific_confidences:
                if confidence < specific_confidences[object_name]:
                    continue
            else:
                if confidence < confidence_threshold:
                    continue

            # Converter as coordenadas de float para int
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            position = f"{x1} {y1} {x2} {y2}"

            # Dicionário básico de informações do objeto
            object_info = {
                'name': object_name,
                'position': position,
                'confidence': confidence
            }

            # Verificar se é "painel-carro" ou "numero-serie" e chamar os scripts correspondentes
            if object_name == "painel-carro":
                odometer = get_odometer(img_path)
                object_info['odometer'] = odometer
            elif object_name == "numero-serie":
                serial_number = get_serial_num(img_path, position)
                object_info['serial_number'] = serial_number

            # Adicionar as informações do objeto à lista
            objects_info.append(object_info)

    if not objects_info:
        print("\nNenhum objeto encontrado.")
        return "unknown"
    else:
        for obj in objects_info:
            print(f"\nObjeto encontrado: {obj['name']}, Confidencia: {obj['confidence']}")
        return objects_info
