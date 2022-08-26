"""Break the problem into several samll steps
1. learn a model that maps (u,y) -> s. u ~ PLANETMASS, y ~ coordinates (r, theta), s ~ steady state
    1.1 DeepONet model
    1.2 PI-DeepONet model
"""
import jax.numpy as jnp
import jaxphyinf


def scale_to_one(u, u_min, u_max):
    u_middle = (u_min + u_max) / 2.0
    return (u - u_middle) / (u_max - u_min) * 2.0


# period boundary condition
def get_period_transform(r_min, r_max):
    def transform(inputs):
        r, theta = jnp.split(inputs, 2, -1)
        """(NUM_BATCH, 1)"""
        return jnp.concatenate(
            (
                scale_to_one(r, r_min, r_max),
                jnp.sin(theta),
                jnp.cos(theta),
            ),
            axis=-1,
        )

    return transform


def get_input_normalization(denominator):
    def transform(inputs):
        return inputs / denominator

    return transform


def build_model(
    Nnode,
    u_net_layer_size,
    y_net_layer_size,
    Nx=1,
    Ndim=2,
    activation="tanh",
    initializer="glorot_uniform",
    u_net_input_transform=None,
    u_net_output_transform=None,
    y_net_input_transform=None,
    y_net_output_transform=None,
    **kwargs,
):
    """

    Args:
        Nnode: Number of neurons of the last layer of u_net (and y_net).
        u_net_layer_size:
        y_net_layer_size:
        Nx: last dimension of the u_net.
            If the deeponet maps one parameter to function, Nx=1 (default).
            If the deeponet maps a vector to function, Nx=len(u).
        Ndim: Dimension of coordinates. If y -> ('r', 'theta'), Ndim=2
        Nout: final_outputs_dim
        activation:
        initializer:
        u_net_input_transform:
        u_net_output_transform:
        y_net_input_transform:
        y_net_output_transform:

    Returns:

    """
    activation = jaxphyinf.get_activation(activation)
    initializer = jaxphyinf.get_initializer(initializer)

    u_net = jaxphyinf.model.MLP(
        inputs_dim=Nx,
        outputs_dim=Nnode,
        layer_size=u_net_layer_size,
        activation=activation,
        w_init=initializer,
    )
    # normalization
    u_net.input_transform = u_net_input_transform
    u_net.output_transform = u_net_output_transform
    u_net.build()

    y_net = jaxphyinf.model.MLP(
        inputs_dim=Ndim,
        outputs_dim=Nnode,
        layer_size=y_net_layer_size,
        activation=activation,
        w_init=initializer,
    )
    # periodic boundary
    # normalization
    y_net.input_transform = y_net_input_transform
    y_net.output_transform = y_net_output_transform

    y_net.build()

    # [2022.05.30] output transform can be do outside this function
    model = jaxphyinf.model.DeepONet(u_net, y_net)

    return model
