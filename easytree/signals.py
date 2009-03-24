from django import dispatch

node_moved = dispatch.Signal(providing_args=["node_moved", "moved_to_node", "relative_position"])
