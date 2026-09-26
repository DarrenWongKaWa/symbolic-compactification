FIGS = fig1_two_workflows fig2_claim_evidence_axes fig3_forward_fail_closed fig4_guo_flagship

all: $(FIGS)

$(FIGS):
	cd $@ && pdflatex -halt-on-error -interaction=nonstopmode figure.tex
	cd $@ && pdftocairo -svg figure.pdf figure.svg

clean:
	for d in $(FIGS); do rm -f $$d/figure.aux $$d/figure.log $$d/figure.out $$d/preview*.png $$d/compile.log; done

.PHONY: all clean $(FIGS)
