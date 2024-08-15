all: README.md

README.md: README.md.in examples/simple.yaml examples/featureful.yaml
	. <(tpl $<) > $@ || { rm -f $@; exit 1; }

clean:
	rm -f README.md
