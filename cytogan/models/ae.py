import os
import time

import numpy as np
import tensorflow as tf
from keras.layers import Dense, Flatten, Input, Reshape
from keras.models import Model
import keras.backend as K

from cytogan.metrics import losses


class AE(object):
    def __init__(self, image_shape, latent_size):
        assert len(image_shape) == 3
        self.image_shape = image_shape
        self.flat_image_shape = np.prod(image_shape)
        self.latent_size = latent_size

        # Variables expected to be set by all models in compile().
        self.session = None
        self.original_images = None
        self.reconstructed_images = None
        self.latent = None
        self.loss = None
        self.optimize = None
        self.learning_rate = None
        self.summary = None
        self.encoder = None
        self.model = None

        self.global_step = tf.Variable(0, trainable=False)
        self.saver = tf.train.Saver(
            max_to_keep=5, keep_checkpoint_every_n_hours=2)

    def compile(self, learning_rate, decay_learning_rate_after,
                learning_rate_decay):
        self.original_images = Input(shape=self.image_shape)
        flat_input = Flatten()(self.original_images)
        self.latent = Dense(self.latent_size, activation='relu')(flat_input)
        decoded = Dense(
            self.flat_image_shape, activation='sigmoid')(self.latent)
        self.reconstructed_images = Reshape(self.image_shape)(decoded)

        self.loss = K.mean(losses.reconstruction_loss(flat_input, decoded))

        self.encoder = Model(self.original_images, self.latent)
        self.model = Model(self.original_images, self.reconstructed_images)

        self.optimize = self._add_optimization_target(
            learning_rate, decay_learning_rate_after, learning_rate_decay)
        self.summary = self._add_summary()

    def save(self, checkpoint_directory):
        if not os.path.exists(checkpoint_directory):
            os.makedirs(checkpoint_directory)
        class_name = self.__class__.__name__
        timestamp = time.strftime('%H-%M-%S_%d-%m-%Y')
        model_key = '{0}-{1}'.format(class_name, timestamp)
        checkpoint_path = os.path.join(checkpoint_directory, model_key)
        self.saver.save(
            self.session, checkpoint_path, global_step=self.global_step)
        print(self.model.layers[1].get_weights())

    def restore(self, checkpoint_directory):
        assert self.session is not None
        checkpoint = tf.train.latest_checkpoint(checkpoint_directory)
        if checkpoint is None:
            raise RuntimeError(
                'Could not find any valid checkpoints under {0}!'.format(
                    checkpoint_directory))
        self.saver.restore(self.session, checkpoint)
        print(self.model.layers[1].get_weights())

    @property
    def is_ready(self):
        return self.model is not None

    def train_on_batch(self, images, summary_writer=None):
        assert self.is_ready
        fetches = [self.optimize, self.loss]
        if summary_writer is not None:
            fetches += [self.summary, self.global_step]
        outputs = self.session.run(
            fetches, feed_dict={self.original_images: images})
        if summary_writer is not None:
            summary_writer.add_summary(
                summary=outputs[2], global_step=outputs[3])
        loss = outputs[1]
        assert np.isscalar(loss)
        return loss

    def encode(self, images):
        assert self.is_ready
        return self.session.run(
            self.encoder.output, feed_dict={self.original_images: images})

    def reconstruct(self, images):
        assert self.is_ready
        return self.session.run(
            self.model.output, feed_dict={self.original_images: images})

    def _add_optimization_target(self, learning_rate,
                                 decay_learning_rate_after,
                                 learning_rate_decay):
        self.learning_rate = learning_rate
        if learning_rate_decay is not None:
            self.learning_rate = tf.train.exponential_decay(
                learning_rate,
                decay_steps=decay_learning_rate_after,
                decay_rate=learning_rate_decay,
                global_step=self.global_step,
                staircase=True)
        return tf.train.AdamOptimizer(self.learning_rate).minimize(
            self.loss, global_step=self.global_step)

    def _add_summary(self):
        tf.summary.histogram('latent', self.latent)
        tf.summary.scalar('loss', self.loss)
        tf.summary.scalar('learning_rate', self.learning_rate)
        tf.summary.image('original', self.original_images, max_outputs=4)
        tf.summary.image(
            'reconstructions', self.reconstructed_images, max_outputs=4)
        return tf.summary.merge_all()

    def __repr__(self):
        assert self.is_ready
        lines = []
        try:
            # >= Keras 2.0.6
            self.model.summary(print_fn=lines.append)
        except TypeError:
            lines = [layer.name for layer in self.model.layers]
        return '\n'.join(map(str, lines))
