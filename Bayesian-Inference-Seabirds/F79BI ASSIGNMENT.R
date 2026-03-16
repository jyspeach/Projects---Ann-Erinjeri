set.seed(8805) 

N <- 1000 #Total population of seabirds
xE <- sample(400:800, 1) #The number of seabirds on island E in year 2

B <- 100000 #Number of iterations to run #Burn in
n <- 500 # Number of samples
m <- 10 #Thinning 

#Initializing vectors for simulation
pE <- vector("numeric", B) #The proportion of seabirds nesting on island E in year 1
delta <- vector("numeric", B) #The probability that a seabird will change from W to E, or from E to W
yE <- vector("numeric", B) #The number of seabirds on island E for both years 1 and 2
yW <- vector("numeric", B) #The number of seabirds on island W for both years 1 and 2

pE[1] <- 0.7 #Initial guess from xE/N
delta[1] <- 0.16 #Initial guess from the prior mean
for (iter in 1:(B - 1)) {
  
  theta_E = pE[iter] * (1 - 2 * delta[iter]) + delta[iter] #The probability that a seabird is on island E in year 2
  theta_W = 1 - theta_E #The probability that a seabird is on island W in year 2
  
  tau_E = ((1 - delta[iter]) * pE[iter]) / theta_E #The probability that a seabird is on island E in year 1 given that it is on island E in year 2
  tau_W = ((1 - delta[iter]) * (1 - pE[iter])) / theta_W #The probability that a seabird is on island W in year 1 given that it is on island W in year 2

  #Augmenting the unobserved data yE and yW using their conditional distributions
  yE[iter + 1] <- rbinom(1, xE, tau_E) #The number of seabirds on island E for both years 1 and 2
  yW[iter + 1] <- rbinom(1, N - xE, tau_W) #The number of seabirds on island W for both years 1 and 2
  
  alpha_pE <- N - xE + yE[iter + 1] - yW[iter + 1] + 1 #The shape parameter for the distribution of pE
  beta_pE <- xE - yE[iter + 1] + yW[iter + 1] + 1 #The rate parameter for the distribution of pE
  
  alpha_delta <- N - yE[iter + 1] - yW[iter + 1] + 2 #The shape parameter for the distribution of delta
  beta_delta <- yE[iter + 1] + yW[iter + 1] + 10 #The rate parameter for the distribution of delta
  
  #Updating pE and delta using conditional distributions
  pE[iter + 1] <- rbeta(1, alpha_pE, beta_pE) 
  delta[iter + 1] <- rbeta(1, alpha_delta, beta_delta)
}

par(mfrow=c(2,2)) 

#Plotting Results

plot(main= "Trace Plot of pE values", xlab="100,000 Simulations",seq(1,B,1), pE , type="l")
hist(main= "Histogram of pE values", xlab = "pE",pE[seq(B-(m*n)+1,B,m)], col = "lightblue")

plot(main= "Trace Plot of delta values", xlab="100,000 Simulations", seq(1,B,1), delta, type="l")
hist(main= "Histogram of delta values",xlab = "delta", delta[seq(B-(m*n)+1,B,m)], col = "pink")

#95% confidence intervals for pE and delta
pE_quantiles <- quantile(pE[seq(B-(m*n)+1,B,m)],probs = c(0.025,0.975))
pE_quantiles
delta_quantiles <- quantile(delta[seq(B-(m*n)+1,B,m)],probs = c(0.025,0.975))
delta_quantiles

#Numerical summaries for pE and delta

sd(pE[seq(B-(m*n)+1,B,m)])
summary(pE[seq(B-(m*n)+1,B,m)])


sd(delta[seq(B-(m*n)+1,B,m)])
summary(delta[seq(B-(m*n)+1,B,m)])

#Checking for correlation between pE and delta 
plot(main = "pE vs. delta", xlab="pE", ylab= "delta",pE[seq(B-(m*n)+1,B,m)], delta[seq(B-(m*n)+1,B,m)])
cor(pE[seq(B-(m*n)+1,B,m)],delta[seq(B-(m*n)+1,B,m)])

#Checking the skewness of both distributions
library(e1071)
skewness(pE[seq(B-(m*n)+1,B,m)])
skewness(delta[seq(B-(m*n)+1,B,m)])


