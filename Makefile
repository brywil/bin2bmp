default:
	@echo "Nothing to do.  Try 'sudo make install'."
clean:
	@echo "Nothing to do. This is not yet a compiled program."
install:
	install -D -m 755 bin2bmp.py ${DESTDIR}/usr/bin/bin2bmp
	ln -sf bin2bmp ${DESTDIR}/usr/bin/bmp2bin
