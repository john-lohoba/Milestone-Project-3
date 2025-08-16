const estimatedUpdate = document.getElementById("estimatedUpdate");
const weekTarget = document.getElementById("weekTarget");
const totalDelivered = document.getElementById("totalDelivered");

const targets = document.getElementsByClassName("target");
const credits = document.getElementsByClassName("credits");

var targetsArray = [];
for(let target of targets){
    targetsArray.push(parseFloat(target.innerText));
}

var creditsArray = [];
for(let credit of credits){
    creditsArray.push(parseFloat(credit.innerText));
}

// Calculates the sum of targets
const initialValue = 0;
const sumOfTargets = targetsArray.reduce((accumulator, currentValue) => accumulator + currentValue, initialValue);
weekTarget.innerText = sumOfTargets;

// Calculates the sum of credits
const sumOfCredits = creditsArray.reduce((accumulator, currentValue) => accumulator + currentValue, initialValue);
totalDelivered.innerText = sumOfCredits;

// Estimated Update message
let update = Number(sumOfCredits - sumOfTargets).toFixed(2);
if (update < 0){
    estimatedUpdate.innerText = `${update}`;
} else{
    estimatedUpdate.innerText = update;
}