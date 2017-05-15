define([
    'jquery',
    'base/js/dialog',
    'base/js/events',
    'base/js/namespace',
], function (
    $,
    dialog,
    events,
    Jupyter
) {
    "use strict";

    var mod_name = 'provenance';
    var log_prefix = '[' + mod_name + ']';
    var options = { // updated from server's config & nb metadata
        run_on_kernel_ready: true,
    };

    var load_ipython_extension = function() {
        // setup things to run on loading config/notebook
        Jupyter.notebook.config.loaded
            .then(function update_options_from_config () {
                $.extend(true, options, Jupyter.notebook.config[mod_name]);
            }, function (reason) {
                console.warn(log_prefix, 'error loading config:', reason);
            })
            .then(function () {
                if (Jupyter.notebook._fully_loaded) {
                    callback_notebook_loaded();
                }
                events.on('notebook_loaded.Notebook', callback_notebook_loaded);
            }).catch(function (reason) {
                console.error(log_prefix, 'unhandled error:', reason);
            });
    };
    
    function handle_output(data){
	    //data is the object passed to the callback from the kernel execution
	    console.log(data);
    };

    var callbacks = {
	    iopub : {
		    output : handle_output,
	    }
    };

    function kernel_ready()
    {
	console.log(Jupyter.notebook);
	var python_command = "import git, os; NOTEBOOK_PATH=os.environ['PWD']; repo = git.Repo(NOTEBOOK_PATH); global PROVENANCE_GIT_SHA; global NOTEBOOK_NAME; global PROVENANCE_GIT_URL; PROVENANCE_GIT_SHA = repo.head.object.hexsha if not (repo == None) else ''; PROVENANCE_GIT_URL = list(repo.remotes['origin'].urls)[0] if not (repo == None) else ''; NOTEBOOK_NAME='" + Jupyter.notebook.notebook_name +"'; print('Hello From Kernel')";
	console.log(python_command);
	Jupyter.notebook.kernel.execute(python_command, callbacks);
    };

    function callback_notebook_loaded () {
	    // update from metadata
        var md_opts = Jupyter.notebook.metadata[mod_name];
        if (md_opts !== undefined) {
            console.log(log_prefix, 'updating options from notebook metadata:', md_opts);
            $.extend(true, options, md_opts);
        }

        if (options.run_on_kernel_ready) {
            if (!Jupyter.notebook.trusted) {
                dialog.modal({
                    title : 'Initialization cells in untrusted notebook',
                    body : 'This notebook is not trusted, so provenance can not be established.',
                    buttons: {'OK': {'class' : 'btn-primary'}},
                    notebook: Jupyter.notebook,
                    keyboard_manager: Jupyter.keyboard_manager,
                });
                return;
            }

            if (Jupyter.notebook && Jupyter.notebook.kernel && Jupyter.notebook.kernel.info_reply.status === 'ok') {
                // kernel is already ready
		kernel_ready();
	    }
            // whenever a (new) kernel  becomes ready, run all initialization cells
            events.on('kernel_ready.Kernel', kernel_ready);
        }
    }

    return {
        load_ipython_extension : load_ipython_extension
    };
});
