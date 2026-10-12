from legacy import frame_length_00, frame_length_08, encode_frame, decode_frame

assert frame_length_00("abc") == 3
assert frame_length_08("abcd") == 4
assert encode_frame("abc") == b"\x03abc"
assert decode_frame(encode_frame("hello")) == "hello"
print("public checks passed")
