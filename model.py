import os

import tensorflow as tf
from tensorflow import keras

print(tf.version.VERSION)
# Recreate the exact same model, including its weights and the optimizer
new_model = tf.keras.models.load_model('mymodel.h5')

# Show the model architecture
print(new_model.summary())
