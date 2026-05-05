const screens = {
    home: renderHome,
    // dream: renderDream,
    // analysis: renderAnalysis,
    // soundscape: renderSoundscape,
};

function renderHome(data) {
    
}

function render(state) {
    const fn = screens[state.screen];
    if (fn) fn(state.screenData);
}

vm.subscribe(render);