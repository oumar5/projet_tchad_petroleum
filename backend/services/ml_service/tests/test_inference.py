import numpy as np

from services.ml_service.app.services.inference import InferenceService


def test_inference_predict_passthrough(tmp_path):
    svc = InferenceService(str(tmp_path))

    class FakeModel:
        def predict(self, X):
            return np.array([1, 2, 3])

    out = svc.predict(FakeModel(), np.zeros((3, 2)))
    assert out.tolist() == [1, 2, 3]
