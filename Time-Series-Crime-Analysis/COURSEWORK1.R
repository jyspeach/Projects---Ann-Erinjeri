#R CODE FOR CW 1 

#Q1
setwd("/Users/annerinjeri/Desktop/TIME SERIES AND MACHINE LEARNING") #Setting directory
crime_rate=read.csv("gotham-crime-rate.csv", header = T) #Reading the crime data from the csv file
attach(crime_rate) 



#Plotting the crime data 
plot(crime_rate,type = "l", col = "blue", 
     main = "Figure 1 - Gotham City Crime Rate over the Years",
     xlab = "Years", ylab = "Crime Rate")

#Identifying max and min crime rate years
max_crime = which.max(Crime.Rate)
min_crime = which.min(Crime.Rate)

#Adding points at the max and min crime rates
points(max_crime, Crime.Rate[max_crime], col = "red", pch = 19, cex = 1.3)
points(min_crime, Crime.Rate[min_crime], col = "darkgreen", pch = 19, cex = 1.3)

#Adding text labels for the max and min crime rates
text(95, 49,
     labels = paste0("Highest Crime Rate\n", round(Crime.Rate[max_crime],3), " in ", Time[max_crime], "th year."),
     pos = 3, cex = 0.8, col = "red")

text(min_crime, 9,
     labels = paste0("Lowest Crime Rate\n", round(Crime.Rate[min_crime],3), " in ", Time[min_crime], "nd year."),
     pos = 1, cex = 0.8, col = "darkgreen")

#Adding dotted line for mean
abline(h = mean(Crime.Rate), col = "black", lwd = 2, lty = 2)

#Label for the mean 
text(60, mean(Crime.Rate) + 2,
     labels = paste0("Mean = ", round(mean(Crime.Rate), 3)),
     col = "black", cex = 0.8)

summary(Crime.Rate)
sd(Crime.Rate)

#Q2
#Taking the logarithm transform
log_crime = log(Crime.Rate)
#Plotting the logarithm transform
plot(log_crime, type = "l", col = "blue",
     main = "Figure 2 - Log-transformed Crime Rate of Gotham City over the Years",
     xlab = "Years", ylab = "log(Crime Rate)")

#Q3
#Applying first order differencing to the log-transformed data
diff_log_crime = diff(log_crime)
#Plotting first order differenced log-transformed data
plot(diff_log_crime, type = "l", col = "blue",
     main = "Figure 3 - First Differenced Log-transformed Crime Rate",
     xlab = "Years", ylab = "Differenced log(Crime Rate)")

#Adding lines for mean, mean +/- 2*SD to show stationarity
abline(h = mean(diff_log_crime), col = "black", lwd = 2, lty = 1)
abline(h = mean(diff_log_crime) + 2*sd(diff_log_crime), col = "black", lty = 3)
abline(h = mean(diff_log_crime) - 2*sd(diff_log_crime), col = "black", lty = 3)

#Adding legend for lines 
legend("topright",
       legend = c("Differenced log(Crime Rate)", "Mean", "Mean ±2 Standard Deviation"),
       col = c("blue", "black", "darkgray"),
       lty = c(1, 1, 3), lwd = c(2, 2, 1), cex = 0.8)

#Q4
par(mfrow=c(1,2)) #Setting layout
#Plotting the sample ACF of the differenced and transformed crime data up to 20 lags.
acf(diff_log_crime, lag.max = 20, main = "Figure 4 - ACF of Differenced Log Data")
#Plotting the sample PACF of the differenced and transformed crime data up to 20 lags.
pacf(diff_log_crime, lag.max = 20, main = "Figure 5 - PACF of Differenced Log Data")

#Q5
#Comparing the AIC and BIC of Model 1 and Model 2
model1 = Arima(log_crime, order = c(0,1,3), include.drift = TRUE)
model2 = Arima(log_crime, order = c(1,1,0), include.drift = TRUE)
AIC(model1)
AIC(model2)
BIC(model1)
BIC(model2)

#Q6 
#Reporting the AIC of proposed Model 2
AIC(model2) 

#Q7
#Extracting the parameters from the summary
summary(model2)

#Q8
#Fitting Model 3 (BATMAN'S MODEL)
model3 = Arima(log_crime, order = c(2,1,1), include.drift = TRUE)
summary(model3)
#Comparing Model 2 and Model 3
AIC(model3)
AIC(model2)
BIC(model3)
BIC(model2)
