"""Node-local reference fine-tuning. Output must not be submitted as a global update."""
import logging
from federated.strategies.fedavg import parameters
from optimization.common.validation import ValidationError, object_fields, integer, nonnegative_number

LOGGER = logging.getLogger(__name__)


def validate_config(config):
    config = object_fields(config, required={'enabled', 'local_epochs', 'learning_rate'}, optional=set(), path='personalization')
    if type(config['enabled']) is not bool:
        raise ValidationError('enabled must be a boolean')
    epochs = integer(config['local_epochs'], 'local_epochs', 1)
    rate = nonnegative_number(config['learning_rate'], 'learning_rate')
    if epochs > 100 or not 0 < rate <= 1:
        raise ValidationError('Invalid personalization training limits')
    return config


def personalize(client, global_model, config):
    config = validate_config(config)
    epochs, rate = config["local_epochs"], config["learning_rate"]
    model = parameters(global_model)
    if config['enabled']:
        model = client.train(model, round_id=1, model_version=0,
                             local_epochs=epochs, learning_rate=rate)['parameters']
    LOGGER.info('local_personalization enabled=%s', config['enabled'])
    return {'scope': 'node_local_only', 'enabled': config['enabled'], 'parameters': model}
