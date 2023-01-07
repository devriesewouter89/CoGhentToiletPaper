import cv2

# Load the template image
template = cv2.imread('template.jpg', 1)
print(template.shape)
# Convert the template image to grayscale
gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

# Apply image filtering to improve the contrast and remove noise
filtered_template = cv2.bilateralFilter(gray_template, 2, 75, 75)

# Threshold the image to create a binary image
ret, thresh = cv2.threshold(filtered_template, 200, 255, cv2.THRESH_BINARY)

# Display the result
cv2.imshow('template', template)
cv2.imshow('gray_template', gray_template)
cv2.imshow('filtered_template', filtered_template)
cv2.imshow('thresh', thresh)
cv2.imwrite('thresh_template.jpg', thresh)
cv2.waitKey(0)

'''
This code will first convert the template image to grayscale, which is necessary for some image processing operations. 
It will then apply a bilateral filter to the grayscale image to improve the contrast and remove noise. 
Finally, it will threshold the filtered image to create a binary image, which is a simple representation of the template
 image with only two pixel values (0 and 255).

You can adjust the parameters of the bilateral filter and the thresholding operation to suit the specific needs of your 
template image. For example, you may need to adjust the values of sigmaColor and sigmaSpace in the call 
to cv2.bilateralFilter to achieve the desired level of noise reduction. Similarly, you may need to adjust the 
value of threshold in the call to cv2.threshold to achieve the desired level of binarization.
'''
