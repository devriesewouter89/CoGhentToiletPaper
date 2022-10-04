Target: prepare an image to be 2D plotted

Problem: images are mostly camera pictures, high res. Thus we need to convert it to line art to be able to plot it.

Found a cool repo: artline, If combined with some tracing programs, this was a good way to go to generate my lineart. Yet due to need of cuda to be able to run it, or need pytorch compiled for CPU. I had a rpi4 lying around, yet immediately getting pytorch (old version!) functioning gave problems with torchvision. I then started looking for some nvidia jetsons, yet apparantly covid chip shortage isn't over yet... So either I had to wait for some jetsons, or recompile pytorch, or go for another approach...

I found a different repo which did 

