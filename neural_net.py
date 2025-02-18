"""
Neural Net logic.
"""

# System Imports.
import datetime, json, keras, numpy

# User Class Imports.
from resources import logging


# Initialize logging.
logger = logging.get_logger(__name__)


class RecurrentNet():
    """
    Recurrent Neural Net using the Keras library.
    """
    def __init__(self, data_source='trump'):
        logger.info('Starting Recurrent Net.')

        self.model = None
        self.data = None

        self.unique_char_set = None
        self.max_string_length = 0
        self.char_to_int_dict = {}
        self.int_to_char_dict = {}

        self.import_data(data_source)
        self.get_character_set()
        self.build_architecture()

    def __del__(self):
        logger.info('Recurrent Net finished.')

    def import_data(self, data_source='trump'):
        """
        Read through and import contents of tweets.

        Twitter was chosen due to all data having limited message length.
        Trump Tweets were chosen due to being generally one of the most documented and well archived accounts.
        :return: Array of tweet messages.
        """
        if data_source == 'trump':
            logger.info('Using Trump Tweet Dataset.')
            file_location = 'Documents/trump_tweets_2017.json'
        elif data_source == 'alice':
            logger.info('Using Alice in Wonderland Dataset.')
            file_location = 'Documents/alice.json'
        else:
            logger.error('Unknown data source.')
            exit(1)

        try:
            file = open(file_location, 'r')

            dataset_import = json.load(file)
            dataset = []

            # Find length of longest individual record in dataset. Use as length for all records.
            # Note that all characters start with escape code '\1'. All characters are end-padded with escape code '\0'.
            for line in dataset_import:
                new_record = len(line['text'])
                if new_record > self.max_string_length:
                    self.max_string_length = new_record
            self.max_string_length += 3
            logger.info('Max record length: {0}'.format(self.max_string_length))

            # For each record in dataset, append until
            for line in dataset_import:
                new_record = '\1'
                new_record += line['text']
                new_record += '\2'
                new_record += '\0'
                dataset.append(new_record)

            file.close()

            # logger.info(dataset)
            self.data = dataset

        except Exception:
            logger.error('Error reading file.')
            logger.error(Exception, exc_info=True)


    def build_architecture(self):
        """
        Build neural net layout.
        """
        self.model = keras.models.Sequential()

        # LSTM layers for recurrent steps.
        # Note: Masking (supposedly) hides null terminating pad character from weights.
        self.model.add(keras.layers.Masking(
            mask_value=self.char_to_int_dict['\0'],
            input_shape=(self.max_string_length, len(self.unique_char_set))
        ))
        self.model.add(keras.layers.LSTM(
            len(self.unique_char_set),
            input_shape=(self.max_string_length, len(self.unique_char_set)),
            return_sequences=True,
            kernel_initializer="one",
        ))
        self.model.add(keras.layers.Dropout(0.2))
        self.model.add(keras.layers.LSTM(
            len(self.unique_char_set),
            return_sequences=True,
        ))
        self.model.add(keras.layers.Dropout(0.2))
        self.model.add(keras.layers.LSTM(
            len(self.unique_char_set),
            return_sequences=True,
        ))
        self.model.add(keras.layers.Dropout(0.2))
        self.model.add(keras.layers.LSTM(
            len(self.unique_char_set),
            return_sequences=True,
        ))
        self.model.add(keras.layers.Dropout(0.2))

        # Dense and activation layers for recurrent steps.
        self.model.add(keras.layers.TimeDistributed(keras.layers.Dense(len(self.unique_char_set))))
        self.model.add(keras.layers.Activation('softmax'))
        self.model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

        self.model.summary()

    def get_character_set(self):
        """
        Creates dictionary of all unique characters in dataset. Also creates reverse translation dict.
        """
        # Create sorted list of all unique characters used in dataset.
        dataset_string = ''.join(self.data)
        self.unique_char_set = sorted(list(set(dataset_string)))

        logger.info('Total Characters: {0}'.format(len(dataset_string)))
        logger.info('Total Records: {0}'.format(len(self.data)))
        logger.info('Unique Char Set: {0}'.format(self.unique_char_set))
        logger.info('Unique Char Count: {0}'.format(len(self.unique_char_set)))

        # # Remove rarely used characters.
        # self.remove_extra_characters(dataset_string)

        # Create Char to Int dictionary.
        for enumeration, value in enumerate(self.unique_char_set):
            self.char_to_int_dict[value] = enumeration
        logger.info('Char to Int Dict: {0}'.format(self.char_to_int_dict))

        # Create Int to Char dictionary.
        for value, enumeration in enumerate(self.unique_char_set):
            self.int_to_char_dict[value] = enumeration
        logger.info('Int to Char Dict: {0}'.format(self.int_to_char_dict))
        logger.info('')
        logger.info('')

    def remove_extra_characters(self, dataset_string, min_required_count=250):
        """
        Remove characters that are rarely used from "possible char set" list.
        :param dataset_string: Full concatenated string of all input data.
        :param min_required_count: Minimum required number of instances that character must show up.
        """
        logger.info('Unique Char Set Before Removal: {0}'.format(self.unique_char_set))
        logger.info('Unique Char Count Before Removal: {0}'.format(len(self.unique_char_set)))

        #
        for char in self.unique_char_set:
            # logger.info('Value: {0}'.format(char))
            if dataset_string.count(char) < min_required_count:
                self.unique_char_set.remove(char)

        logger.info('Unique Char Count After Removal: {0}'.format(len(self.unique_char_set)))
        logger.info('Unique Char Set After Removal: {0}'.format(self.unique_char_set))

    def train(self, num_epochs=1000):
        """
        Train neural net on data.
        """
        # Convert feature and target data into onehots.
        features = numpy.zeros((len(self.data), self.max_string_length, len(self.unique_char_set)))
        targets = numpy.zeros((len(self.data), self.max_string_length, len(self.unique_char_set)))
        for record_index in range(len(self.data)):

            # Set up feature inputs.
            input_sequence = []
            for char in self.data[record_index]:
                input_sequence.append(self.char_to_int_dict[char])

            features[record_index] = self.convert_to_onehot(input_sequence)

            # Set up target inputs.
            output_sequence = []
            for char in self.data[record_index]:
                output_sequence.append(self.char_to_int_dict[char])
            output_sequence.pop(0)
            output_sequence.append(self.char_to_int_dict['\0'])

            targets[record_index] = self.convert_to_onehot(output_sequence)

        # logger.info('Feature Onehot:\n{0}'.format(features))
        # logger.info('Target Onehot:\n{0}'.format(targets))

        # Pad data values.
        features = keras.preprocessing.sequence.pad_sequences(features, maxlen=self.max_string_length)
        targets = keras.preprocessing.sequence.pad_sequences(targets, maxlen=self.max_string_length)

        for index in range(num_epochs):
            logger.info('')
            logger.info('')
            logger.info('Epoch {0}'.format(index))
            self.model.fit(features, targets, batch_size=self.max_string_length, verbose=1)
            if index % 10 == 0:
                generated_values = self.generate_text()
                logger.testresult('Epoch: {0}   Full Generated Int String: {1}'.format(index, generated_values[0]))
                logger.testresult('Epoch: {0}   Full Generated Char String: {1}'.format(index, generated_values[1]))
            if index % 50 == 0:
                self.model.save_weights(
                    'Documents/Weights/4LSTM_Size{0}_atEpoch{1}_{2}'
                        .format(len(self.unique_char_set), index, datetime.datetime.now().strftime('%y-%m-%d_%I:%M')))

    def convert_to_onehot(self, sequence):
        """
        Convert sequence to onehot.
        :param sequence: Sequence to convert.
        :return: Onehot of sequence.
        """
        new_onehot = numpy.zeros((self.max_string_length, len(self.unique_char_set)))
        # for char_index in range(self.max_string_length):
        for char_index in range(len(sequence)):
            new_onehot[char_index][sequence[char_index]] = 1
        return new_onehot

    def append_onehot(self, old_onehot, row_index, char):
        """
        Changes a single row of given onehot.
        :param old_onehot: Onehot to modify.
        :param row_index: Row of onehot to modify.
        :param char: New char value to set row to.
        :return: Modified onehot.
        """
        new_row = numpy.zeros((1, len(self.unique_char_set)))
        new_row[0][self.char_to_int_dict[char]] = 1

        try:
            # logger.info('Old Row {0}: {1}'.format(row_index, old_onehot[0][row_index]))
            old_onehot[0][row_index] = new_row
            # logger.info('New Row {0}: {1}'.format(row_index, old_onehot[0][row_index]))
        except IndexError:
            pass # If index error occurs, then should be end of string anyway.
        return old_onehot

    def generate_text(self):
        """
        Attempts to create new text based off of trained data.
        :return: The full generated text. Is in tuple form, with
        """
        logger.info('Attempting to generate text.')
        generated_text = numpy.zeros((1, self.max_string_length, len(self.unique_char_set)))
        generated_text[0] = self.append_onehot(generated_text, 0, '\1')
        generated_char_string = ''
        generated_int_string = ''
        for index in range(self.max_string_length):
            try:
                predict_value = self.model.predict(generated_text)[0]
                predict_value = numpy.argmax(predict_value[index])

                # logger.info('Predicted Value: {0}({1})'.format(predict_value, self.int_to_char_dict[predict_value]))
                generated_text[0] = self.append_onehot(generated_text, (index + 1), self.int_to_char_dict[predict_value])
            except IndexError:
                pass  # If index error occurs, then should be end of string anyway.

            # Display generated string values.
            generated_char_string = ''
            generated_int_string = ''
            for test_index in range(len(generated_text[0])):
                conversion_index = None
                for onehot_index in range(len(generated_text[0][test_index])):
                    if generated_text[0][test_index][onehot_index] == 1:
                        conversion_index = onehot_index
                        break
                try:
                    generated_char_string += self.int_to_char_dict[conversion_index]
                    generated_int_string += str(conversion_index) + ' '
                except KeyError:
                    break
        # logger.info('Full Generated String: {0}'.format(generated_int_string))
        # logger.info('Full Generated String: {0}'.format(generated_char_string))
        return (generated_int_string, generated_char_string)

    def import_weights(self, location):
        """
        Load in previously saved weights. If used, should be called before training.
        :param location: Location of saved weights.
        """
        self.model.load_weights(location)
        self.model.summary()
