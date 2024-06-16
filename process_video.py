
def calculate_iou(box1, box2):
    """
    Calculate the Intersection over Union (IoU) of two bounding boxes.
    Each box is represented by a dictionary with keys: x, y, width, height.
    """

    x1_min = box1['x'] - box1['width'] / 2
    y1_min = box1['y'] - box1['height'] / 2
    x1_max = box1['x'] + box1['width'] / 2
    y1_max = box1['y'] + box1['height'] / 2

    x2_min = box2['x'] - box2['width'] / 2
    y2_min = box2['y'] - box2['height'] / 2
    x2_max = box2['x'] + box2['width'] / 2
    y2_max = box2['y'] + box2['height'] / 2

    inter_x_min = max(x1_min, x2_min)
    inter_y_min = max(y1_min, y2_min)
    inter_x_max = min(x1_max, x2_max)
    inter_y_max = min(y1_max, y2_max)

    intersection_area = max(0, inter_x_max - inter_x_min) * max(0, inter_y_max - inter_y_min)

    box1_area = box1['width'] * box1['height']
    box2_area = box2['width'] * box2['height']

    iou = intersection_area / float(box1_area + box2_area - intersection_area)
    return iou

def find_closest(pred1, pred2):
    """
    Match bounding boxes from pred1 to pred2 using IoU metric.
    """
    matches = {}
    for i, box1 in enumerate(pred1):
        best_match = None
        best_iou = 0
        for j, box2 in enumerate(pred2):
          if abs(box1['x']-box2['x']) <= threshold and pred1['class_id'] == pred2['class_id']:
            iou = calculate_iou(box1, box2)
            if iou > best_iou:
                best_iou = iou
                best_match = j
        if best_match is None:
            matches[i] = not_found
        else:
          matches[i] = j

    return matches

def predict(frame): # questa la predict "base" per avere tutto più compatto
  return model.predict(frame).json()['predictions']

def detect_defects(frame):

    # DA SISTEMARE
    # # frame_str = json.dumps(frame)
    # cur = predict(frame)
    # v = 1 # da inizializzare a un valore sensato
    # if prev:
    #     m = find_closest(cur,prev)
    # else:
    #     m = {}
    # for i in range(len(m)):
    #     # ricorda che m è un hash map tra gli indici di cur e prev
    #     if v and m[i] != not_found and prev[m[i]]['confidence'] >= confidence_threshold:
    #         x = 1/(k+1)*(cur[i]['x']+prev[m[i]]['x'])
    #         # qua lo sbatti è che dovrei fare il return_closest k volte, da provare (per ora cosi ha senso solo per k = 1)
    #         y = 1/2*(cur[i]['y']+prev[m[i]]['x'] + v / fps) # v o v/fps?
    #     else:
    #         x = cur[i]['x']
    #         y = cur[i]['y']

    #     class_id = cur['class_id']
    #     x0 = int(x - cur['width'] / 2)
    #     x1 = int(x + cur['width'] / 2)
    #     y0 = int(y - cur['height'] / 2)
    #     y1 = int(y + cur['height'] / 2)
    #     color = color_map.get(class_id, (255, 255, 255))
    #     cv2.rectangle(frame, (x0, y0), (x1, y1), color, 4)

    #     # v.update(cur)

    # # prev.popleft() # non va la deque bro
    # prev.append(cur)
    return frame

