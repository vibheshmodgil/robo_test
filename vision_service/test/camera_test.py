import cv2

for i in range(10):

    print(f"Testing camera {i}")

    cap = cv2.VideoCapture(i)

    success, frame = cap.read()

    print("Success:", success)

    if success and frame is not None:

        cv2.imwrite(
            f"camera_{i}.jpg",
            frame
        )

        print("Saved frame")

    cap.release()