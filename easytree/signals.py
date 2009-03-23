from django import dispatch

node_moved = dispatch.Signal(providing_args=["moved_node", "moved_to_node", "relative_position"])
