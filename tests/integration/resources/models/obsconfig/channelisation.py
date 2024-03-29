"""."""

from ska_tmc_cdm.messages.central_node.sdp import Channel, ChannelConfiguration

from .target_spec import ArraySpec, BaseTargetSpec, TargetSpecs

DEFAULT_CHANNELS = {
    "vis_channels": ChannelConfiguration(
        channels_id="vis_channels",
        spectral_windows=[
            Channel(
                spectral_window_id="fsp_1_channels",
                count=4,
                start=0,
                stride=2,
                freq_min=0.35e9,
                freq_max=0.368e9,
                link_map=[[0, 0], [200, 1], [744, 2], [944, 3]],
            )
        ],
    )
}


class Channelization(TargetSpecs):
    """A class representing Channelisation."""

    def __init__(
        self,
        channels: list[ChannelConfiguration] | None = None,
        base_target_specs: dict[str, BaseTargetSpec] | None = None,
        array: ArraySpec | None = None,
    ) -> None:
        """Init object.

        :param: channels: _description_
        :type array: list[ChannelConfiguration] | None
        :param: base_target_specs: _description_
        :type array: dict[str, BaseTargetSpec] | None
        :param: array: _description_
        :type array: ArraySpec | None
        """
        TargetSpecs.__init__(self, base_target_specs, array)
        if channels is not None:
            self._channel_configurations = {
                **{channel.channels_id: channel for channel in channels},
            }
        else:
            self._channel_configurations = DEFAULT_CHANNELS

    def add_channel_configuration(self, config_name: str, spectral_windows: list[Channel]):
        """Add channel configuration.

        :param: config_name: configuration name
        :type config_name: str
        :param: spectral_windows: spectral windows
        :type spectral_windows: list[Channel]
        """
        assert (
            self._channel_configurations.get(config_name) is None
        ), f"configuration {config_name} already exists."
        self._channel_configurations[config_name] = ChannelConfiguration(
            channels_id=config_name, spectral_windows=spectral_windows
        )

    @property
    def channel_configurations(self) -> list[str]:
        """Return channel configurations.

        :return: _description_
        :rtype: _type_
        """
        return list(self._channel_configurations.keys())

    @channel_configurations.setter
    def channel_configurations(self, new_config: dict[str, ChannelConfiguration]):
        """Set channel configurations.

        :param: new_config: new configuration
        """
        self._channel_configurations = new_config

    def get_channel_configuration(self, config_name: str) -> ChannelConfiguration:
        """Get channel configurations.

        :param: config_name: configuration name
        :type config_name: str
        :returns: _description_
        :rtype: ChannelConfiguration
        """
        assert (
            self._channel_configurations.get(config_name) is not None
        ), f"configuration {config_name} does not exist."
        return self._channel_configurations[config_name]

    @property
    def target_spec_channels(self):
        """Return target spec channels.

        :return: _description_
        :rtype: _type_
        """
        return {target.channelisation for target in self.target_specs.values()}

    @property
    def channels(self) -> list[ChannelConfiguration]:
        """Return channels.

        :return: _description_
        :rtype: _type_
        """
        unique_keys = self.target_spec_channels
        return [
            channel_config
            for channel_config in [self._channel_configurations.get(key) for key in unique_keys]
            if channel_config
        ]
