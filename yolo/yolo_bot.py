import os
import cv2
import numpy as np
import pyautogui
from inference_sdk import InferenceHTTPClient, InferenceConfiguration

# Connect to workflow (once, before the loop)
print("starting...")

client = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key=os.environ["ROBOFLOW_API_KEY"],   # set it first: export ROBOFLOW_API_KEY=...
).configure(InferenceConfiguration(api_key_transport="header"))

shot_w = pyautogui.screenshot().width   # screenshot width (e.g. 2880)
mouse_w = pyautogui.size().width        # mouse width (e.g. 1440)
scale = shot_w / mouse_w                # usually 2 on a Mac


# Loop: screenshot -> send to workflow -> show
print("loaded, running loop")
while True:
    frame = np.array(pyautogui.screenshot())
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    h, w = frame.shape[:2]       # NEW: get the screen size
    frame = frame[:, :w // 2]    # NEW: keep only the left half

    result = client.run_workflow(
        workspace_name="nickcancode-s-workspace",
        workflow_id="clickthedot-vclickthedot-1-rfdetr-nas-t1-9602f1-logic",
        images={"image": frame},
        use_cache=True
    )

    #find dot and click it
    print(result)
    preds = result[0]["predictions"]["predictions"]   # list of dots found
    if len(preds) > 0:
        dot = max(preds, key=lambda p: p["confidence"])  # most confident dot
        x = dot["x"] / scale
        y = dot["y"] / scale
        pyautogui.click(x, y)
        print("clicked", int(x), int(y), round(dot["confidence"], 2))    

    cv2.imshow("screen", cv2.resize(frame, None, fx=0.4, fy=0.4))
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()