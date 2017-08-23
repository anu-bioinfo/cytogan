import keras.backend as K
import keras.optimizers
import numpy as np
from keras.layers import Dense, Flatten, Input, Reshape
from keras.models import Model


class AE(object):
    def __init__(self, image_shape, latent_size):
        original_images = Input(shape=image_shape)
        flat_images = Flatten()(original_images)
        latent = Dense(latent_size, activation='relu')(flat_images)
        decoded = Dense(np.prod(image_shape), activation='sigmoid')(latent)
        reconstruction = Reshape(image_shape)(decoded)

        self.encoder = Model(original_images, latent)
        self.model = Model(original_images, reconstruction)
        # Can be overriden as a method by subclasses.
        self._loss = 'binary_crossentropy'

    @property
    def learning_rate(self):
        assert hasattr(self, 'optimizer'), 'must call prepare() first'
        exp = (1. / (1. + self.optimizer.decay * self.optimizer.iterations))
        return K.eval(self.optimizer.lr * exp)

    def prepare(self, learning_rate, decay_learning_rate_after,
                learning_rate_decay):
        # TF treats the decay as a factor every N steps, while for Keras it's d
        # in lr^(1 / (1 + d * iterations)).
        self.optimizer = keras.optimizers.Adam(
            lr=learning_rate, decay=1 - learning_rate_decay)
        print('Using {0} loss'.format(self._loss))
        self.model.compile(loss=self._loss, optimizer=self.optimizer)

    def train_on_batch(self, images):
        return self.model.train_on_batch(images, images)

    def reconstruct(self, images):
        latent_vectors = self.encoder.predict(images)
        reconstructions = self.model.predict(images)
        return latent_vectors, reconstructions