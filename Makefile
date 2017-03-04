default:
	@echo "Nothing to do.  Try 'sudo make install'."
clean:
	@echo "Nothing to do. This is not yet a compiled program."
install:
	cp bin2bmp.py bin2bmp
	install -m 755 bin2bmp ${DESTDIR}/usr/bin/
